# qrrobo

A câmera é o olho. O QR Code é um bilhete. Esta biblioteca lê o bilhete e, se vocês quiserem, manda a palavra até o bloco LEGO ou RaspberryPI.

O movimento não vem pronto. A função de andar, girar ou balançar a placa é de vocês.

Funciona no notebook (Windows) e no Raspberry Pi. A câmera pode ser a do notebook, uma webcam ou a câmera do Pi. O bloco SPIKE Prime ou Robot Inventor, com firmware Pybricks, recebe a palavra pelo cabo ou pelo Bluetooth.

## Instalar

```powershell
python -m pip install qrrobo
```

## Dicionário

Tudo começa criando um robô. Sem essa linha, o resto não existe:

```python
from qrrobo import Robo

robo = Robo()
```

`Robo()` é a ficha do robô: qual correio usar e qual câmera abrir. Os comandos abaixo são dessa ficha.

- **`Robo(conexao=..., camera=...)`** cria o robô. Ainda não liga a câmera nem procura o bloco.
- **`@robo.quando("FRENTE")`** grava uma regra: se o bilhete disser `FRENTE`, chame a função escrita embaixo. A palavra do QR e a palavra entre aspas precisam ser a mesma.
- **`robo.esperar()`** abre a câmera e fica olhando, sem parar, até alguém apertar **Q** (Que encerra o app). Cada bilhete novo dispara a função do `quando`.
- **`robo.ler()`** abre a câmera, espera um bilhete e devolve a palavra. Não fica no laço e não procura o bloco. **Q** devolve um texto vazio (ou seja, encerra o app).
- **`robo.enviar("FRENTE")`** manda essa palavra ao bloco SPIKE. Não mexe em motor. Quem mexe é o programa que já está rodando no bloco.

`esperar` é como se fosse a aula inteira com a câmera aberta, aguardando algo. `ler` é uma única espiada: mostrou o QR, recebeu a palavra, a janela fecha.

## A câmera

`camera` é o número da câmera no computador. O padrão é `0`, a primeira que o sistema encontrar.

```python
robo = Robo(camera=0)   # a primeira: webcam do notebook ou a câmera do Pi
robo = Robo(camera=1)   # a segunda, se houver outra webcam
robo = Robo(camera=2)   # a terceira
```

Não existe nome de câmera aqui, só esses números. Se a janela abrir preta ou na câmera errada, troque o número.

## A conexão

`conexao` diz se existe um bloco e por onde o correio vai. Também se escolhe na hora de criar o robô. No resumo, você escolhe a forma que deseja conectar-se

```python
robo = Robo()                        # tenta o cabo; se não achar, tenta o Bluetooth
robo = Robo(conexao="auto")          # a mesma coisa
robo = Robo(conexao="usb")           # só o cabo de dados
robo = Robo(conexao="bluetooth")     # só o Bluetooth
robo = Robo(conexao="nenhuma")       # sem bloco: só a câmera
```

Dá para juntar câmera com:

```python
robo = Robo(conexao="bluetooth", camera=0)
robo = Robo(conexao="usb", camera=1)
```

`enviar` só funciona quando a conexão é `"auto"`, `"usb"` ou `"bluetooth"` e o bloco foi achado. Com `"nenhuma"`, `enviar` avisa que não há bloco.

O cabo precisa transmitir dados. Cabo que só carrega não serve. No Bluetooth, fechem o app do SPIKE e a aba do Pybricks antes de rodar: o bloco só atende um correio por vez. Em algumas ocasioes especiais, vale a pena fechar o Pybricks e ligar apenas o bluetooth para testar.

## Movimento no computador

A função do `quando` roda no notebook ou no Raspberry. Serve para um `print`, para um motor ligado no próprio Pi, ou para qualquer código Python de vocês. é praticamente: Quando aparecer "andar" > ande.

```python
from qrrobo import Robo

robo = Robo(conexao="nenhuma")

def andar():
    print("as rodas giram")

@robo.quando("FRENTE")
def frente():
    andar()

robo.esperar()
```

## Movimento no SPIKE

`robo.enviar` só conversa com SPIKE Prime ou Robot Inventor com firmware Pybricks. A biblioteca não anda, não gira e não conhece porta de motor. Ela entrega a palavra. O movimento fica no programa do bloco, no arquivo por exemplo [examples/modelo_bloco.py](examples/modelo_bloco.py).

No computador:

```python
from qrrobo import Robo

robo = Robo(conexao="bluetooth")

@robo.quando("FRENTE")
def frente():
    robo.enviar("FRENTE")

@robo.quando("GIRAR")
def girar():
    robo.enviar("GIRAR")

robo.esperar()
```

No bloco, vocês completam o que cada palavra faz:

```python
def frente():
    # o movimento de vocês, com os motores do SPIKE
    print("FRENTE")

def girar():
    print("GIRAR")

ACOES = {
    "FRENTE": frente,
    "GIRAR": girar,
}
```

Ordem da aula: gravem esse programa no bloco, fechem o site do Pybricks, apertem o botão do bloco para ele ficar esperando e só então rode o programa do computador.

O Raspberry com câmera usa o mesmo código. Se o Pi for o robô e os motores estiverem nele, usem `conexao="nenhuma"` e chamem o movimento dentro do `quando`, sem `enviar`.

## Uma leitura só

A câmera vê o mesmo bilhete muitas vezes por segundo. `esperar` obedece uma vez. Para obedecer de novo, tirem o QR da frente e mostrem outra vez.

```python
from qrrobo import Robo

robo = Robo(conexao="nenhuma")
palavra = robo.ler()
print("Li:", palavra)
```

## Onde isto roda

- Notebook Windows e Raspberry Pi, com Python 3.
- Câmera do notebook, webcam USB ou câmera do Pi.
- SPIKE Prime ou Robot Inventor com firmware Pybricks, no cabo de dados ou no Bluetooth.

Não roda dentro do bloco. Não conversa com o app oficial do SPIKE. O firmware Pybricks se instala uma vez em [code.pybricks.com](https://code.pybricks.com), com um cabo que transmita dados.

## Problemas comuns

- **Não achei o bloco.** Feche o app do SPIKE e o site do Pybricks. O bloco precisa estar ligado e perto. A procura dura cerca de 20 segundos. `Ctrl+C` no meio avisa "Procura cancelada" e para, sem encher o terminal.
- **O nome que aparece é SPIKE, não Pybricks.** O firmware ainda é o da LEGO. Instale o Pybricks.
- **Cabo não funciona.** Use um cabo de dados, ou `conexao="bluetooth"`.
- **A palavra chegou e o robô não mexeu.** O movimento está na função de vocês. No SPIKE, essa função está no programa do bloco. No Pi, ela está dentro do `quando`.
- **`enviar` reclamou que não há bloco.** O `Robo` foi criado com `conexao="nenhuma"`.
- **A janela abre na câmera errada.** Troque `camera=0` por `camera=1`.
