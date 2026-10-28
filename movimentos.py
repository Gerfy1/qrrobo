from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Stop
from pybricks.tools import wait, StopWatch

# ---------------------------------------------------------------
# Configuração do robô
# ---------------------------------------------------------------
hub = PrimeHub()

def ligar_motor(porta, sentido=None, avisar=True):
    """Cria o motor se ele estiver na porta. Porta vazia não derruba o programa."""
    try:
        if sentido is None:
            return Motor(porta)
        return Motor(porta, sentido)
    except OSError:
        if avisar:
            print("Sem motor na porta", porta)
        return None


# A placa é movida pelos motores B e F.
# Se ela for para o lado errado, troque o sinal de VELOCIDADE_PLACA.
motor_esquerdo = ligar_motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_direito = ligar_motor(Port.F, Direction.CLOCKWISE)

garra_e = None
garra_a = None

VELOCIDADE_PLACA = 150
TEMPO_MAX_PLACA = 1200  # ms: o movimento acaba mesmo sem encostar no fim

# Constantes de correção ao andar reto
GANHO_ERRO = -1.2      # parte "P"
GANHO_VARIACAO = 1   # parte "D"

# Constantes do giro preciso
GIRO_KP = 1.2
GIRO_KD =0.00000000000001
GIRO_POTENCIA_MIN = 12
GIRO_TOLERANCIA = 0.7
GIRO_TEMPO_MAX = 1000    # se o giro não assentar, ele espera até esse tempo (ms)

# Pausas entre movimentos (ms). Antes eram 300 e 200.
PAUSA_ANTES = 50
PAUSA_DEPOIS = 0

# Constantes das garras
GARRA_VELOCIDADE = 300   # graus/s (velocidade padrão)
GARRA_FORCA = 60         # limite de potência (%) ao fechar contra a peça
# Sentido que FECHA cada garra: 1 ou -1. Se alguma abrir quando
# deveria fechar, troque o sinal dela.
SENTIDO_FECHAR_E = 1
SENTIDO_FECHAR_A = -1


# ---------------------------------------------------------------
# Garras
# ---------------------------------------------------------------
def mover_garra(motor, graus, velocidade=GARRA_VELOCIDADE, esperar=True):
    """
    Move uma garra um número de graus e a mantém travada na posição.
    velocidade: graus/s
    esperar: False = a garra se mexe em segundo plano e o código segue.
    """
    if motor is None:
        print("Essa garra não está conectada.")
        return
    motor.run_angle(velocidade, graus, then=Stop.HOLD, wait=esperar)


def _ir_ate_acabar(velocidade):
    """Gira B e F juntos até encostar no fim ou até estourar o tempo.

    Encostar no canto não é erro: os motores freiam e o apito não entra.
    """
    motor_esquerdo.run(velocidade)
    motor_direito.run(velocidade)

    cronometro = StopWatch()
    travado = 0
    while cronometro.time() < TEMPO_MAX_PLACA:
        if motor_esquerdo.stalled() or motor_direito.stalled():
            travado += 1
        else:
            travado = 0
        if travado >= 3:
            print("Encostou no limite. Movimento encerrado.")
            break
        wait(30)
    else:
        print("Tempo do movimento acabou.")

    motor_esquerdo.brake()
    motor_direito.brake()
    wait(150)


def balancar_placa():
    """Leva a placa para a frente e volta uma vez, com os motores B e F."""
    if motor_esquerdo is None or motor_direito is None:
        print("Faltam os motores nas portas B e F.")
        return

    print("Placa para a frente.")
    _ir_ate_acabar(VELOCIDADE_PLACA)
    print("Placa de volta.")
    _ir_ate_acabar(-VELOCIDADE_PLACA)
    print("Placa parada.")


def abrir_garras(graus=90, velocidade=GARRA_VELOCIDADE, esperar=True):
    """Abre as duas garras ao mesmo tempo, na velocidade pedida (graus/s)."""
    if garra_e is None or garra_a is None:
        print("Falta garra na porta A ou E.")
        return
    garra_e.run_angle(velocidade, -SENTIDO_FECHAR_A * graus, then=Stop.HOLD, wait=False)
    garra_a.run_angle(velocidade, -SENTIDO_FECHAR_E * graus, then=Stop.HOLD, wait=False)
    if esperar:
        while not (garra_e.done() and garra_a.done()):
            wait(10)


def fechar_garras(velocidade=GARRA_VELOCIDADE, forca=GARRA_FORCA):
    """
    Fecha as duas garras até encostar na peça (motor travar) e
    continua segurando com força limitada.
    velocidade: graus/s   |   forca: limite de potência em %
    """
    if garra_e is None or garra_a is None:
        print("Falta garra na porta A ou E.")
        return
    garra_e.run_until_stalled(SENTIDO_FECHAR_A * velocidade, then=Stop.HOLD, duty_limit=forca)
    garra_a.run_until_stalled(SENTIDO_FECHAR_E * velocidade, then=Stop.HOLD, duty_limit=forca)


# ---------------------------------------------------------------
# Andar reto usando o giroscópio
# ---------------------------------------------------------------
def andar_reto(velocidade, graus):
    """
    Anda para frente (ou para trás, com velocidade negativa)
    mantendo o robô reto com o giroscópio.
    """
    if motor_esquerdo is None or motor_direito is None:
        print("Faltam as rodas nas portas B e F.")
        return
    motor_esquerdo.brake()
    motor_direito.brake()
    wait(PAUSA_ANTES)

    motor_direito.reset_angle(0)
    hub.imu.reset_heading(0)

    erro_anterior = 0

    while abs(motor_direito.angle()) < graus:
        erro = hub.imu.heading()
        correcao = erro * GANHO_ERRO + GANHO_VARIACAO * (erro_anterior - erro)

        motor_esquerdo.dc(velocidade + correcao)
        motor_direito.dc(velocidade - correcao)

        erro_anterior = erro
        wait(10)

    motor_esquerdo.brake()
    motor_direito.brake()
    wait(PAUSA_DEPOIS)


# ---------------------------------------------------------------
# Giro preciso usando o giroscópio (lógica mantida)
# ---------------------------------------------------------------
def girar(angulo, potencia_max=50):
    """
    Gira o robô parado no lugar.
    Positivo = direita (horário), negativo = esquerda.
    """
    if motor_esquerdo is None or motor_direito is None:
        print("Faltam as rodas nas portas B e F.")
        return
    motor_esquerdo.brake()
    motor_direito.brake()
    wait(PAUSA_ANTES)

    hub.imu.reset_heading(0)

    erro_anterior = angulo
    ciclos_no_alvo = 0
    cronometro = StopWatch()

    while ciclos_no_alvo < 8 and cronometro.time() < GIRO_TEMPO_MAX:
        erro = angulo - hub.imu.heading()

        if abs(erro) <= GIRO_TOLERANCIA:
            ciclos_no_alvo += 1
            motor_esquerdo.brake()
            motor_direito.brake()
        else:
            ciclos_no_alvo = 0
            direcao = 1 if erro > 0 else -1

            potencia = abs(erro) * GIRO_KP + GIRO_KD * (abs(erro) - abs(erro_anterior))
            potencia = min(potencia, potencia_max)
            potencia = max(potencia, GIRO_POTENCIA_MIN)

            motor_esquerdo.dc(direcao * potencia)
            motor_direito.dc(-direcao * potencia)

        erro_anterior = erro
        wait(2)

    motor_esquerdo.brake()
    motor_direito.brake()
    wait(PAUSA_DEPOIS)


# ---------------------------------------------------------------
# Exemplo de uso
# Só roda quando este arquivo é o programa principal.
# Quando o ouvinte.py importa as funções, a missão não dispara sozinha.
# ---------------------------------------------------------------
if __name__ == "__main__":
    andar_reto(-70, 820)
    girar(-56, 50)
    andar_reto(-70, 1190)
    girar(93, 70)
    andar_reto(-30, 185)
    andar_reto(70, 220)
    girar(-85, 70)
    andar_reto(40, 590)
    andar_reto(-40, 450)
    girar(130, 70)
    andar_reto(-50, 400)
    girar(-90, 50)

