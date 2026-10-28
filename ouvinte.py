from usys import stdin

from movimentos import balancar_placa

print("Esperando FRENTE ou DANCAR.")

while True:
    comando = stdin.readline()
    if not comando:
        break

    comando = comando.strip()
    print("Bloco recebeu:", comando)

    if comando == "FRENTE" or comando == "DANCAR":
        balancar_placa()
    elif comando == "SAIR":
        break
