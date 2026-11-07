from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime,
    ForeignKey, Text, Index, CheckConstraint, text
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


def utcnow() -> datetime:
    """Datetime UTC naive (banco guarda UTC sem tz). Centraliza para evitar deprecação de utcnow()."""
    from datetime import timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Dinheiro: SEMPRE Numeric, nunca float (RN/§7)
MONEY = Numeric(10, 2, asdecimal=True)


class Admin(Base):
    __tablename__ = "administradores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=utcnow, nullable=False)

    historicos = relationship("HistoricoAdmin", back_populates="administrador")


class ProdutoPrincipal(Base):
    __tablename__ = "produtos_principais"
    __table_args__ = (
        CheckConstraint("quantidade_desejada >= 0", name="ck_produto_qtd_desejada"),
        CheckConstraint("quantidade_comprada_externa >= 0", name="ck_produto_qtd_comprada"),
        CheckConstraint("preco_atual >= 0", name="ck_produto_preco"),
    )

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), nullable=True, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    imagem_url = Column(String(1000), nullable=True)
    produto_url = Column(String(1000), nullable=True)
    categoria = Column(String(100), nullable=True)
    # RN-01 v2: fralda — tamanho (RN+, P, M, G...) e ordem de exibição dos grupos
    tamanho = Column(String(30), nullable=True)
    ordem_exibicao = Column(Integer, default=0, nullable=False)
    # RN-08 v2: preço pode ser nulo (Amazon mostra "Ver opções"); admin informa manualmente
    preco_atual = Column(MONEY, nullable=True)
    preco_anterior = Column(MONEY, nullable=True)
    preco_sincronizado_em = Column(DateTime, nullable=True)
    quantidade_desejada = Column(Integer, default=1, nullable=False)
    quantidade_comprada_externa = Column(Integer, default=0, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=utcnow, nullable=False)

    numeros = relationship("Numero", back_populates="produto_principal")


class Mimo(Base):
    __tablename__ = "mimos"
    __table_args__ = (
        CheckConstraint("quantidade_desejada >= 0", name="ck_mimo_qtd_desejada"),
        CheckConstraint("quantidade_comprada_externa >= 0", name="ck_mimo_qtd_comprada"),
        CheckConstraint("preco_atual >= 0", name="ck_mimo_preco"),
    )

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), nullable=True, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    imagem_url = Column(String(1000), nullable=True)
    produto_url = Column(String(1000), nullable=True)
    categoria = Column(String(100), nullable=True)
    preco_atual = Column(MONEY, nullable=True)  # pode ser nulo até o admin informar (RN-08 v2)
    preco_anterior = Column(MONEY, nullable=True)
    preco_sincronizado_em = Column(DateTime, nullable=True)
    quantidade_desejada = Column(Integer, default=1, nullable=False)
    quantidade_comprada_externa = Column(Integer, default=0, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=utcnow, nullable=False)

    reservas = relationship("Reserva", back_populates="mimo")


class Numero(Base):
    __tablename__ = "numeros"
    __table_args__ = (
        CheckConstraint("numero >= 1", name="ck_numero_positivo"),
        CheckConstraint(
            "status IN ('disponivel','reservado','confirmado','compra_externa')",
            name="ck_numero_status"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, index=True, nullable=False)
    produto_principal_id = Column(Integer, ForeignKey("produtos_principais.id"), nullable=True)
    # disponivel, reservado, confirmado, compra_externa (RN-10: cinza, origem registrada)
    status = Column(String(30), default="disponivel", index=True, nullable=False)
    # RN-10: origem da ocupação por compra externa (ex.: "Comprada direto na Amazon")
    origem_ocupacao = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=utcnow, nullable=False)

    produto_principal = relationship("ProdutoPrincipal", back_populates="numeros")
    reservas = relationship("Reserva", back_populates="numero", cascade="all, delete-orphan")


class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        CheckConstraint(
            "status IN ('reservada','confirmada','expirada','cancelada')",
            name="ck_reserva_status"
        ),
        CheckConstraint(
            "forma_presente IN ('amazon','pix','local')",
            name="ck_reserva_forma_presente"
        ),
        CheckConstraint(
            "forma_mimo IN ('amazon','pix','local')",
            name="ck_reserva_forma_mimo"
        ),
        CheckConstraint("valor_pix_total >= 0", name="ck_reserva_pix_total"),
        # INTEGRIDADE CRÍTICA: no máximo UMA reserva ativa (não expirada/cancelada/confirmada...)
        # por número. 'reservada' é o único estado que ocupa o número; confirmada/expirada/cancelada
        # são terminais e o status do próprio Numero impede re-reserva indevida.
        Index(
            "uq_reserva_ativa_por_numero",
            "numero_id",
            unique=True,
            postgresql_where=text("status = 'reservada'"),
            sqlite_where=text("status = 'reservada'"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    numero_id = Column(Integer, ForeignKey("numeros.id"), nullable=False, index=True)
    mimo_id = Column(Integer, ForeignKey("mimos.id"), nullable=False, index=True)
    nome_convidado = Column(String(150), nullable=False)
    whatsapp = Column(String(30), nullable=False)
    autoriza_nome_publico = Column(Boolean, default=False, nullable=False)

    # LGPD: consentimento registrado com versão do texto e data
    consentimento_versao = Column(String(20), nullable=False, default="v1")
    consentimento_em = Column(DateTime, default=utcnow, nullable=False)

    # Formas independentes: 'amazon' ou 'pix' (RN-04)
    forma_presente = Column(String(20), nullable=False)
    forma_mimo = Column(String(20), nullable=False)

    # Preços congelados na reserva (RN-08)
    preco_presente_reserva = Column(MONEY, nullable=False, default=0)
    preco_mimo_reserva = Column(MONEY, nullable=False, default=0)
    valor_pix_total = Column(MONEY, nullable=False, default=0)

    # Status: 'reservada', 'confirmada', 'expirada', 'cancelada' (RN-07)
    status = Column(String(30), default="reservada", index=True, nullable=False)

    criada_em = Column(DateTime, default=utcnow, nullable=False)
    expira_em = Column(DateTime, nullable=False, index=True)
    confirmada_em = Column(DateTime, nullable=True)

    # Acompanhamento sem login: guardamos apenas o HASH do token (nunca o token puro)
    token_acompanhamento_hash = Column(String(128), nullable=True, index=True)

    numero = relationship("Numero", back_populates="reservas")
    mimo = relationship("Mimo", back_populates="reservas")
    comprovantes = relationship("Comprovante", back_populates="reserva", cascade="all, delete-orphan")
    historicos = relationship("HistoricoAdmin", back_populates="reserva")


class Comprovante(Base):
    __tablename__ = "comprovantes"
    __table_args__ = (
        CheckConstraint(
            "tipo_item IN ('presente','mimo')",
            name="ck_comprovante_tipo"
        ),
        CheckConstraint(
            "forma_aquisicao IN ('amazon','pix','local')",
            name="ck_comprovante_forma"
        ),
        CheckConstraint(
            "status IN ('aguardando_envio','recebido','aprovado','rejeitado')",
            name="ck_comprovante_status"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_item = Column(String(20), nullable=False)  # 'presente' ou 'mimo'
    forma_aquisicao = Column(String(20), nullable=False)  # 'amazon' ou 'pix'
    status = Column(String(30), default="aguardando_envio", nullable=False)  # aguardando_envio, recebido, aprovado, rejeitado
    observacao_admin = Column(Text, nullable=True)
    comprovante_url = Column(String(1000), nullable=True)  # Suporte futuro a upload (serviço de armazenamento abstrato)
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
    criado_em = Column(DateTime, default=utcnow, nullable=False)

    administrador = relationship("Admin", back_populates="historicos")
    reserva = relationship("Reserva", back_populates="historicos")


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(100), unique=True, index=True, nullable=False)
    valor = Column(Text, nullable=False)
    atualizado_em = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Sincronizacao(Base):
    __tablename__ = "sincronizacoes"
    __table_args__ = (
        CheckConstraint(
            "fonte IN ('manual_import','amazon_sync')",
            name="ck_sincronizacao_fonte"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    fonte = Column(String(50), nullable=False)  # 'manual_import' | 'amazon_sync'
    resultado = Column(Text, nullable=False)
    erros = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=utcnow, nullable=False)
