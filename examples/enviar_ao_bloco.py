"""O olho lê o bilhete e o correio leva a mesma palavra ao bloco.

O bloco precisa já estar com o programa de vocês rodando.
Feche o app do SPIKE e a aba do Pybricks antes de começar.
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
