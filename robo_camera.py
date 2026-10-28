"""A câmera lê o QR e manda a palavra ao bloco.

O bloco já precisa estar com o programa de vocês rodando.
Feche o app do SPIKE e a aba do Pybricks antes de começar.
Aperte Q na janela da câmera para sair.
"""

from qrrobo import Robo

robo = Robo()


@robo.quando("FRENTE")
def frente():
    print("Mandando FRENTE ao bloco.")
    robo.enviar("FRENTE")


@robo.quando("DANCAR")
def dancar():
    print("Mandando DANCAR ao bloco.")
    robo.enviar("DANCAR")


robo.esperar()
