"""Olho (câmera) e correio (cabo ou Bluetooth) do robô.

O movimento não mora aqui. A turma escreve a função e decide o que a palavra faz.
"""

from __future__ import annotations

import asyncio
import sys

QUADROS_PARA_LIBERAR = 20
JANELA = "Olho do robo"
CONEXOES = ("auto", "usb", "bluetooth", "nenhuma")


def preparar_console() -> None:
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class Robo:
    """A câmera lê o bilhete. O correio leva a palavra até o bloco, se ele existir."""

    def __init__(self, conexao: str = "auto", camera: int = 0) -> None:
        if conexao not in CONEXOES:
            raise ValueError(
                "conexao deve ser 'auto', 'usb', 'bluetooth' ou 'nenhuma'."
            )
        self.conexao = conexao
        self.camera_indice = camera
        self._funcoes: dict[str, callable] = {}
        self._hub = None
        self._ultimo = ""
        self._sumiu = 0
        self._envios: list[asyncio.Task] = []

    def quando(self, texto: str, funcao=None):
        """Registra o que fazer quando o bilhete trouxer esta palavra.

        Dá para usar como decorador:

            @robo.quando("FRENTE")
            def frente():
                ...
        """
        chave = str(texto).strip().upper()

        def registrar(fn):
            self._funcoes[chave] = fn
            return fn

        if funcao is not None:
            return registrar(funcao)
        return registrar

    def esperar(self) -> None:
        """Abre a câmera e fica obedecendo os bilhetes até a tecla Q."""
        preparar_console()
        self._rodar(self._esperar())

    def ler(self) -> str:
        """Abre a câmera e devolve a próxima palavra nova. Q devolve texto vazio.

        Não procura o bloco. Serve para testar o olho sozinho.
        """
        preparar_console()
        return self._rodar(self._ler_um())

    def _rodar(self, tarefa):
        """Roda o laço. Ctrl+C vira uma frase, sem o traceback do Bluetooth."""
        try:
            return asyncio.run(tarefa)
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise SystemExit("Encerrado.")

    def enviar(self, texto: str) -> None:
        """Entrega uma palavra ao bloco. Não cria movimento nenhum."""
        if self._hub is None:
            raise RuntimeError(
                "Não há bloco conectado. "
                "Crie o Robo com conexao 'auto', 'usb' ou 'bluetooth'."
            )
        mensagem = str(texto).strip()
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._hub.write_line(mensagem))
            return
        self._envios.append(asyncio.create_task(self._hub.write_line(mensagem)))

    def _bilhete_novo(self, comando: str) -> str:
        """Devolve a palavra só na primeira vez. Cartão parado não repete."""
        if not comando:
            self._sumiu += 1
            if self._sumiu > QUADROS_PARA_LIBERAR:
                self._ultimo = ""
            return ""
        self._sumiu = 0
        if comando == self._ultimo:
            return ""
        self._ultimo = comando
        return comando

    async def _esperar(self) -> None:
        import cv2

        await self._conectar()
        camera, leitor = self._abrir_camera(cv2)
        print("Cada QR vale uma leitura. Tire o cartão da frente para ler de novo.")
        print("Aperte Q na janela para sair.")
        try:
            while True:
                comando, quadro = self._quadro(cv2, camera, leitor)
                if comando:
                    print(f"Li o bilhete: {comando}")
                    funcao = self._funcoes.get(comando)
                    if funcao is not None:
                        funcao()
                        await self._enviar_pendentes()
                    elif self._funcoes:
                        print("Ninguém se cadastrou para esta palavra.")
                if quadro is not None:
                    cv2.imshow(JANELA, quadro)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                    break
                await asyncio.sleep(0)
        finally:
            camera.release()
            cv2.destroyAllWindows()
            await self._desconectar()

    async def _ler_um(self) -> str:
        import cv2

        camera, leitor = self._abrir_camera(cv2)
        print("Mostre um QR Code. Aperte Q para cancelar.")
        try:
            while True:
                comando, quadro = self._quadro(cv2, camera, leitor)
                if quadro is not None:
                    cv2.imshow(JANELA, quadro)
                if comando:
                    return comando
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                    return ""
                await asyncio.sleep(0)
        finally:
            camera.release()
            cv2.destroyAllWindows()

    def _abrir_camera(self, cv2):
        camera = cv2.VideoCapture(self.camera_indice)
        if not camera.isOpened():
            raise SystemExit(
                "Não consegui abrir a câmera. "
                "Feche outro programa que a esteja usando ou tente Robo(camera=1)."
            )
        return camera, cv2.QRCodeDetector()

    def _quadro(self, cv2, camera, leitor):
        ok, quadro = camera.read()
        if not ok or quadro is None:
            return "", None
        texto, _, _ = leitor.detectAndDecode(quadro)
        comando = self._bilhete_novo((texto or "").strip().upper())
        aviso = comando or "Mostre um QR    |    Q sai"
        cv2.putText(
            quadro,
            aviso,
            (16, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return comando, quadro

    async def _conectar(self) -> None:
        if self.conexao == "nenhuma":
            print("Sem bloco. A câmera só lê o bilhete.")
            return
        if self.conexao in ("auto", "usb"):
            hub = await self._conectar_usb()
            if hub is not None:
                self._hub = hub
                print("Bloco conectado pelo cabo.")
                return
            if self.conexao == "usb":
                raise SystemExit(
                    "Não achei o bloco no cabo. "
                    "Use um cabo que transmita dados e o firmware Pybricks."
                )
        self._hub = await self._conectar_bluetooth()
        print("Bloco conectado pelo Bluetooth.")

    async def _conectar_usb(self):
        try:
            from usb.core import find as find_usb

            from pybricksdev.connections.pybricks import PybricksHubUSB
            from pybricksdev.usb import (
                EV3_USB_PID,
                LEGO_USB_VID,
                MINDSTORMS_INVENTOR_USB_PID,
                NXT_USB_PID,
                SPIKE_ESSENTIAL_USB_PID,
                SPIKE_PRIME_USB_PID,
            )
        except ImportError:
            return None

        portas = {
            NXT_USB_PID,
            EV3_USB_PID,
            SPIKE_PRIME_USB_PID,
            SPIKE_ESSENTIAL_USB_PID,
            MINDSTORMS_INVENTOR_USB_PID,
        }

        def eh_pybricks(aparelho) -> bool:
            if aparelho.idVendor != LEGO_USB_VID or aparelho.idProduct not in portas:
                return False
            try:
                nome = aparelho.product
            except ValueError:
                return False
            return bool(nome and nome.endswith("Pybricks"))

        backend = None
        try:
            import libusb_package
            import usb.backend.libusb1

            backend = usb.backend.libusb1.get_backend(
                find_library=libusb_package.find_library
            )
        except Exception:
            backend = None

        try:
            aparelho = find_usb(backend=backend, custom_match=eh_pybricks)
        except Exception as erro:
            print("O cabo não levou o correio:", erro)
            return None
        if aparelho is None:
            return None
        try:
            hub = PybricksHubUSB(aparelho)
            await hub.connect()
        except Exception as erro:
            print("O cabo não levou o correio:", erro)
            return None
        return hub

    async def _conectar_bluetooth(self):
        from bleak import BleakScanner
        from pybricksdev.ble import find_device
        from pybricksdev.connections.pybricks import PybricksHubBLE

        print("Procurando o bloco pelo Bluetooth...")
        print("Deixe o hub ligado, perto do computador, e feche o app do SPIKE.")
        try:
            aparelho = await find_device(timeout=20)
        except asyncio.TimeoutError:
            print("Não apareceu nenhum bloco com firmware Pybricks.")
            try:
                await self._listar_bluetooth(BleakScanner)
            except Exception as erro:
                print("Não consegui listar o Bluetooth:", erro)
            raise SystemExit(1)
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise SystemExit("Procura cancelada. O bloco não foi conectado.")
        except Exception as erro:
            print("O Bluetooth não levou o correio:", erro)
            print("Ligue o Bluetooth do computador e deixe o hub perto.")
            raise SystemExit(1)
        hub = PybricksHubBLE(aparelho)
        try:
            await hub.connect()
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise SystemExit("Procura cancelada. O bloco não foi conectado.")
        except Exception as erro:
            print("Achei o bloco, mas a conexão não abriu:", erro)
            print("Feche o app do SPIKE e a aba do Pybricks. O bloco só atende um correio por vez.")
            raise SystemExit(1)
        return hub

    async def _listar_bluetooth(self, scanner) -> None:
        print("Aparelhos Bluetooth vistos agora:")
        aparelhos = await scanner.discover(timeout=8)
        if not aparelhos:
            print("  nenhum. Ligue o Bluetooth do computador e o bloco.")
            return
        for aparelho in aparelhos:
            print(f"  {aparelho.name or '(sem nome)'}")
        print("O app do SPIKE usa outro Bluetooth.")
        print("Este correio só acha o bloco depois do firmware Pybricks.")

    async def _enviar_pendentes(self) -> None:
        while self._envios:
            await self._envios.pop(0)

    async def _desconectar(self) -> None:
        if self._hub is not None:
            await self._hub.disconnect()
            self._hub = None
