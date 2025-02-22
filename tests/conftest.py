import pytest
import pandas as pd
import os
import json
from app import app, db
from app.models import Firewall

@pytest.fixture
def test_app():
    """테스트용 Flask 앱 fixture"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_client(test_app):
    """테스트용 클라이언트 fixture"""
    return test_app.test_client()

@pytest.fixture
def mock_ngf_data():
    """NGF 테스트 데이터 fixture"""
    data_path = os.path.join(os.path.dirname(__file__), 'test_data', 'ngf_sample_data.json')
    with open(data_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def mock_mf2_data():
    """MF2 테스트 데이터 fixture"""
    data_path = os.path.join(os.path.dirname(__file__), 'test_data', 'mf2_sample_data.json')
    with open(data_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def mock_paloalto_data():
    """PALOALTO 테스트 데이터 fixture"""
    data_path = os.path.join(os.path.dirname(__file__), 'test_data', 'paloalto_sample_data.json')
    with open(data_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def sample_firewall(test_app):
    """테스트용 방화벽 데이터 fixture"""
    firewall = Firewall(
        name='Test Firewall',
        type='ngf',
        ip_address='192.168.1.1',
        username='test_user',
        password='test_password'
    )
    db.session.add(firewall)
    db.session.commit()
    return firewall 