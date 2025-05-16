import random
import time
import datetime
import json
import os
from zoneinfo import ZoneInfo

fusohorario = ZoneInfo("America/Sao_Paulo")
id_inversor = "I-0123456789"
arquivo_horario = "horarios.json"
arquivo_diario = "diarios.json"

# E = t * V * A
def simulate_energy():
    volt = random.randint(10, 20)
    amper = random.randint(10, 20)
    # retorna energia em joules (assumindo 3600s por hora)
    return volt * amper * 3600

def garantir_arquivo(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)

def criar_bloco_horario(energy_j):
    agora = datetime.datetime.now(fusohorario)
    ts = agora.replace(minute=0, second=0, microsecond=0)
    return {
        "inversor": id_inversor,
        "timestamp": ts.isoformat(),
        "energia": energy_j
    }

def agregar_dia_anterior(lista_blocos):
    ontem_str = (datetime.datetime.now(fusohorario) - datetime.timedelta(days=1)).date().isoformat()
    # filtra só os blocos de ontem
    blocos_ontem = [b for b in lista_blocos if b["timestamp"].startswith(ontem_str)]
    # soma corretamente a energia
    total = sum(b["energia"] for b in blocos_ontem)
    bloco_diario = {
        "inversor": id_inversor,
        "data": ontem_str,
        "energia_total_j": total,
        "detalhes_horarios": blocos_ontem
    }
    # mantém apenas os blocos que não são de ontem
    blocos_restantes = [b for b in lista_blocos if b not in blocos_ontem]
    return bloco_diario, blocos_restantes

def carregar(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def salvar(path, dados):
    with open(path, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def segundos_ate_proxima_hora():
    agora = datetime.datetime.now(fusohorario)
    proxima = (agora + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return (proxima - agora).total_seconds()

def main():
    # garante que os arquivos existam
    garantir_arquivo(arquivo_horario)
    garantir_arquivo(arquivo_diario)

    blocos_horarios = carregar(arquivo_horario)
    blocos_diarios = carregar(arquivo_diario)

    while True:
        # espera até o início da próxima hora
        time.sleep(segundos_ate_proxima_hora())

        # gera e salva bloco horário
        energia = simulate_energy()
        bloco = criar_bloco_horario(energia)
        blocos_horarios.append(bloco)
        salvar(arquivo_horario, blocos_horarios)

        # se já for meia-noite, agrega o dia anterior
        agora = datetime.datetime.now(fusohorario)
        if agora.hour == 0 and agora.minute == 0:
            diario, resto = agregar_dia_anterior(blocos_horarios)
            blocos_diarios.append(diario)
            salvar(arquivo_diario, blocos_diarios)

            blocos_horarios = resto
            salvar(arquivo_horario, blocos_horarios)

if __name__ == "__main__":
    main()
