from flask import render_template
from app import app

@app.route('/')
def index():
    return render_template('index.html', title='FPAT')

@app.route('/policy')
def policy():
    return render_template('policy/index.html', title='정책 관리')

@app.route('/analysis')
def analysis():
    return render_template('analysis/index.html', title='정책 분석')

@app.route('/firewall')
def firewall():
    return render_template('firewall/index.html', title='방화벽 관리')