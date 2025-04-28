import time
import datetime

def calcular_energia(voltage, current_mA, tempo_segundos):
    corrente_A = current_mA / 1000  # Convertendo mA para A
    potencia_W = voltage * corrente_A
    tempo_horas = tempo_segundos / 10
    energia_Wh = potencia_W * tempo_horas
    return energia_Wh

def coletar_dados():
    # Simular leitura da célula solar (no futuro, substituir pela leitura real)
    voltage = 5.0      # Valor simulado (em Volts)
    current_mA = 100   # Valor simulado (em miliampères)

    tempo_segundos = 10  # 1 hora

    energia = calcular_energia(voltage, current_mA, tempo_segundos)

    # Obter horário atual
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Salvar no arquivo
    with open("dados_hora.txt", "a") as arquivo:
        arquivo.write(f"{agora},{voltage},{current_mA},{energia:.3f}\n")

    print(f"[{agora}] Energia gerada: {energia:.3f} Wh")

if __name__ == "__main__":
    while True:
        coletar_dados()
        time.sleep(10)  # Espera 1 hora (para testes pode mudar para 10 segundos)
