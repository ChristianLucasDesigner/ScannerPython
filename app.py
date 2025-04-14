from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from scanner import escanear_rede, salvar_csv
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from auth import login_required, verificar_credenciais
import pandas as pd
from openpyxl import Workbook
import json
import os
from auth import USUARIOS

app = Flask(__name__)
app.secret_key = "chave_super_secreta_do_painel"

# Histórico de varreduras
HISTORICO_FILE = "historico.json"
historico = []

# Carregar histórico se existir
if os.path.exists(HISTORICO_FILE):
    with open(HISTORICO_FILE, 'r') as f:
        historico = json.load(f)

def salvar_historico():
    with open(HISTORICO_FILE, 'w') as f:
        json.dump(historico, f)

# ⏱️ Agendador automático
def tarefa_automatica():
    print("🔁 Rodando varredura automática...")
    try:
        resultados = escanear_rede("192.168.200")
        salvar_csv(resultados)
        historico.append({
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "usuario": "Sistema",
            "tipo": "Automático",
            "resultados": len(resultados)
        })
        salvar_historico()
    except Exception as e:
        print(f"Erro na varredura automática: {str(e)}")

scheduler = BackgroundScheduler()
scheduler.add_job(tarefa_automatica, 'interval', minutes=30)
scheduler.start()

# 🔐 Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logado"):
        return redirect(url_for("home"))
        
    erro = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()
        
        if not usuario or not senha:
            erro = "Usuário e senha são obrigatórios"
        else:
            valido, nome = verificar_credenciais(usuario, senha)
            if valido:
                session["logado"] = True
                session["usuario"] = usuario
                session["nome"] = nome
                return redirect(url_for("home"))
            else:
                erro = "Usuário ou senha inválidos"
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# 🏠 Página principal
@app.route("/")
@login_required
def home():
    return render_template("home.html", historico=historico[-5:])

# 📡 Rota de escaneamento
@app.route("/scan", methods=["POST"])
@login_required
def scan():
    # Verificar se já houve uma requisição recente
    if 'ultimo_scan' in session:
        ultimo_scan = datetime.strptime(session['ultimo_scan'], "%Y-%m-%d %H:%M:%S")
        if (datetime.now() - ultimo_scan).total_seconds() < 30:
            return jsonify({"erro": "Aguarde 30 segundos entre os scans"}), 429

    base_ip = request.json.get("base_ip")
    if not base_ip:
        return jsonify({"erro": "IP base não fornecido"}), 400

    try:
        resultados = escanear_rede(base_ip)
        
        # Registrar no histórico
        historico.append({
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "usuario": session.get("nome"),
            "tipo": "Manual",
            "resultados": len(resultados)
        })
        salvar_historico()
        
        # Atualizar timestamp do último scan
        session['ultimo_scan'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "dispositivos": resultados
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/relatorios")
@login_required
def relatorios():
    return render_template("dashboard/relatorios.html", historico=historico)

@app.route("/ips")
@login_required
def ips():
    return render_template("ips.html")

@app.route("/meu_perfil")
@login_required
def meu_perfil():
    usuario_logado = session.get("usuario")
    dados_usuario = USUARIOS.get(usuario_logado, {})
    return render_template("configuracoes/meu_perfil.html", usuario=usuario_logado, dados=dados_usuario)

@app.route("/usuarios")
@login_required
def usuarios():
    return render_template("configuracoes/usuarios.html", usuarios=USUARIOS)

# 📥 Exportar para Excel
@app.route("/exportar", methods=["POST"])
@login_required
def exportar():
    dados = request.json
    if not dados:
        return jsonify({"erro": "Dados não fornecidos"}), 400

    try:
        wb = Workbook()
        ws = wb.active
        
        # Cabeçalhos
        ws.append(["IP", "Hostname", "Status"])
        
        # Dados
        for item in dados.get("dispositivos", []):
            ws.append([item["ip"], item["hostname"], item["status"]])
        
        # Salvar arquivo
        nome_arquivo = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(nome_arquivo)
        
        return jsonify({"arquivo": nome_arquivo})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
