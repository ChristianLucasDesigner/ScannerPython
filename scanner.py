# scanner.py
import subprocess
import socket
import csv
from datetime import datetime
import platform
import time

def verificar_permissao_ping():
    try:
        # Tentar executar um ping para testar permissões
        subprocess.run(["ping", "-n", "1", "127.0.0.1"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      timeout=1)
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False

def escanear_rede(base_ip):
    if not verificar_permissao_ping():
        raise PermissionError("Sem permissão para executar ping. Execute como administrador.")
    
    ativos = []
    print(f"\n📡 Iniciando varredura em {base_ip}.1 a {base_ip}.254...\n")
    
    for i in range(1, 255):
        ip = f"{base_ip}.{i}"
        try:
            # Configurar timeout baseado no sistema operacional
            timeout = 100 if platform.system() == "Windows" else 1
            count = "-n" if platform.system() == "Windows" else "-c"
            
            resultado = subprocess.run(
                ["ping", count, "1", "-w", str(timeout), ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2  # Timeout total de 2 segundos
            )
            
            if "TTL=" in resultado.stdout or "ttl=" in resultado.stdout.lower():
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except (socket.herror, socket.gaierror):
                    hostname = "Hostname não encontrado"
                
                ativos.append({
                    "ip": ip,
                    "hostname": hostname,
                    "status": "ativo"
                })
                print(f"✅ {ip} — {hostname}")
            else:
                print(f"❌ {ip} — Sem resposta")

        except subprocess.TimeoutExpired:
            print(f"⚠️ {ip} — Timeout")
            continue
        except Exception as e:
            print(f"⚠️ Erro ao pingar {ip}: {str(e)}")
            continue
        
        # Pequena pausa entre os pings para não sobrecarregar a rede
        time.sleep(0.1)
    
    print(f"\n🔍 Total de ativos encontrados: {len(ativos)}\n")
    return ativos

def salvar_csv(resultados):
    if not resultados:
        print("⚠️ Nenhum resultado para salvar")
        return
        
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"relatorio_{agora}.csv"
    
    try:
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["ip", "hostname", "status"])
            writer.writeheader()
            for item in resultados:
                writer.writerow(item)
        print(f"📁 Relatório salvo como: {nome_arquivo}")
    except Exception as e:
        print(f"❌ Erro ao salvar relatório: {str(e)}")
