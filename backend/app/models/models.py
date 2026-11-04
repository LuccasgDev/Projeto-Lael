from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Admin(Base):
    __tablename__ = "administradores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    historicos = relationship("HistoricoAdmin", back_populates="administrador")


class ProdutoPrincipal(Base):
    __tablename__ = "produtos_principais"

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), nullable=True, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    imagem_url = Column(String(1000), nullable=True)
    produto_url = Column(String(1000), nullable=True)
    categoria = Column(String(100), nullable=True)
    preco_atual = Column(Float, nullable=False, default=0.0)
    preco_anterior = Column(Float, nullable=True)
    preco_sincronizado_em = Column(DateTime, nullable=True)
    quantidade_desejada = Column(Integer, default=1, nullable=False)
    quantidade_comprada_externa = Column(Integer, default=0, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    numeros = relationship("Numero", back_populates="produto_principal")


class Mimo(Base):
    __tablename__ = "mimos"

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), nullable=True, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    imagem_url = Column(String(1000), nullable=True)
    produto_url = Column(String(1000), nullable=True)
    categoria = Column(String(100), nullable=True)
    preco_atual = Column(Float, nullable=False, default=0.0)
    preco_anterior = Column(Float, nullable=True)
    preco_sincronizado_em = Column(DateTime, nullable=True)
    quantidade_desejada = Column(Integer, default=1, nullable=False)
    quantidade_comprada_externa = Column(Integer, default=0, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    reservas = relationship("Reserva", back_populates="mimo")


class Numero(Base):
    __tablename__ = "numeros"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, index=True, nullable=False)
    produto_principal_id = Column(Integer, ForeignKey("produtos_principais.id"), nullable=True)
    status = Column(String(30), default="disponivel", index=True, nullable=False)  # disponivel, reservado, confirmado
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    produto_principal = relationship("ProdutoPrincipal", back_populates="numeros")
    reservas = relationship("Reserva", back_populates="numero", cascade="all, delete-orphan")


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    numero_id = Column(Integer, ForeignKey("numeros.id"), nullable=False, index=True)
    mimo_id = Column(Integer, ForeignKey("mimos.id"), nullable=False, index=True)
    nome_convidado = Column(String(150), nullable=False)
    whatsapp = Column(String(30), nullable=False)
    autoriza_nome_publico = Column(Boolean, default=False, nullable=False)
    
    # Formas independentes: 'amazon' ou 'pix'
    forma_presente = Column(String(20), nullable=False)
    forma_mimo = Column(String(20), nullable=False)
    
    # Precos congelados
    preco_presente_reserva = Column(Float, nullable=False, default=0.0)
    preco_mimo_reserva = Column(Float, nullable=False, default=0.0)
    valor_pix_total = Column(Float, nullable=False, default=0.0)
    
    # Status: 'reservada', 'confirmada', 'expirada', 'cancelada'
    status = Column(String(30), default="reservada", index=True, nullable=False)
    
    criada_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    expira_em = Column(DateTime, nullable=False, index=True)
    confirmada_em = Column(DateTime, nullable=True)

    numero = relationship("Numero", back_populates="reservas")
    mimo = relationship("Mimo", back_populates="reservas")
    comprovantes = relationship("Comprovante", back_populates="reserva", cascade="all, delete-orphan")
    historicos = relationship("HistoricoAdmin", back_populates="reserva")


class Comprovante(Base):
    __tablename__ = "comprovantes"

    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_item = Column(String(20), nullable=False)  # 'presente' ou 'mimo'
    forma_aquisicao = Column(String(20), nullable=False)  # 'amazon' ou 'pix'
    status = Column(String(30), default="aguardando_envio", nullable=False)  # aguardando_envio, recebido, aprovado, rejeitado
    observacao_admin = Column(Text, nullable=True)
    comprovante_url = Column(String(1000), nullable=True)  # Suporte futuro a upload
    recebido_em = Column(DateTime, nullable=True)
    aprovado_em = Column(DateTime, nullable=True)
    rejeitado_em = Column(DateTime, nullable=True)

    reserva = relationship("Reserva", back_populates="comprovantes")


class HistoricoAdmin(Base):
    __tablename__ = "historico_administrativo"

    id = Column(Integer, primary_key=True, index=True)
    administrador_id = Column(Integer, ForeignKey("administradores.id"), nullable=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id", ondelete="SET NULL"), nullable=True)
    acao = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    administrador = relationship("Admin", back_populates="historicos")
    reserva = relationship("Reserva", back_populates="historicos")


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(100), unique=True, index=True, nullable=False)
    valor = Column(Text, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
