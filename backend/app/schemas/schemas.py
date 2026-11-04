from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# --- Public Schemas ---

class ProdutoPrincipalPublic(BaseModel):
    id: int
    asin: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    imagem_url: Optional[str] = None
    produto_url: Optional[str] = None
    categoria: Optional[str] = None
    preco_atual: float
    preco_anterior: Optional[float] = None
    preco_sincronizado_em: Optional[datetime] = None
    quantidade_desejada: int
    disponibilidade_restante: int

    class Config:
        from_attributes = True


class MimoPublic(BaseModel):
    id: int
    asin: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    imagem_url: Optional[str] = None
    produto_url: Optional[str] = None
    categoria: Optional[str] = None
    preco_atual: float
    preco_anterior: Optional[float] = None
    preco_sincronizado_em: Optional[datetime] = None
    disponibilidade_restante: int

    class Config:
        from_attributes = True


class NumeroGridItem(BaseModel):
    id: int
    numero: int
    status: str  # disponivel, reservado, confirmado
    nome_publico: Optional[str] = None
    produto_nome: Optional[str] = None
    produto_imagem: Optional[str] = None

    class Config:
        from_attributes = True


class NumeroDetailResponse(BaseModel):
    id: int
    numero: int
    status: str
    produto_principal: Optional[ProdutoPrincipalPublic] = None

    class Config:
        from_attributes = True


class ReservaCreateRequest(BaseModel):
    numero_id: int
    mimo_id: int
    nome_convidado: str = Field(..., min_length=2, max_length=150)
    whatsapp: str = Field(..., min_length=10, max_length=30)
    autoriza_nome_publico: bool = False
    forma_presente: str  # 'amazon' ou 'pix'
    forma_mimo: str  # 'amazon' ou 'pix'
    consentimento_lgpd: bool

    @field_validator("whatsapp")
    @classmethod
    def validate_whatsapp(cls, v: str) -> str:
        # Remove non-digits
        digits = re.sub(r"\D", "", v)
        if len(digits) < 10 or len(digits) > 13:
            raise ValueError("O WhatsApp deve conter DDD e número válido (ex: 85999998888)")
        return digits

    @field_validator("forma_presente", "forma_mimo")
    @classmethod
    def validate_forma(cls, v: str) -> str:
        v_clean = v.lower().strip()
        if v_clean not in ["amazon", "pix"]:
            raise ValueError("A forma de aquisição deve ser 'amazon' ou 'pix'")
        return v_clean

    @field_validator("consentimento_lgpd")
    @classmethod
    def validate_lgpd(cls, v: bool) -> bool:
        if not v:
            raise ValueError("O consentimento para uso dos dados na organização do evento é obrigatório")
        return v


class ComprovantePublic(BaseModel):
    id: int
    tipo_item: str
    forma_aquisicao: str
    status: str
    observacao_admin: Optional[str] = None

    class Config:
        from_attributes = True


class ReservaPublicResponse(BaseModel):
    id: int
    numero: int
    nome_convidado: str
    whatsapp: str
    forma_presente: str
    forma_mimo: str
    presente_nome: str
    presente_imagem: Optional[str] = None
    presente_url: Optional[str] = None
    preco_presente_reserva: float
    mimo_nome: str
    mimo_imagem: Optional[str] = None
    mimo_url: Optional[str] = None
    preco_mimo_reserva: float
    valor_pix_total: float
    status: str
    criada_em: datetime
    expira_em: datetime
    whatsapp_link: str
    whatsapp_mensagem: str
    comprovantes: List[ComprovantePublic] = []

    class Config:
        from_attributes = True


class PublicConfigResponse(BaseModel):
    nome_evento: str
    data_evento: str
    whatsapp_casal: str
    chave_pix: str
    tipo_chave_pix: str
    titular_pix: str
    banco_pix: str
    prazo_padrao_horas: int
    total_numeros: int
    mensagem_inicial: Optional[str] = None
    mensagem_confirmacao: Optional[str] = None


# --- Admin Schemas ---

class AdminLoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_id: int
    admin_nome: str
    admin_email: str


class AdminUserResponse(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class ComprovanteAdminResponse(BaseModel):
    id: int
    reserva_id: int
    tipo_item: str
    forma_aquisicao: str
    status: str
    observacao_admin: Optional[str] = None
    recebido_em: Optional[datetime] = None
    aprovado_em: Optional[datetime] = None
    rejeitado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReservaAdminItem(BaseModel):
    id: int
    numero_id: int
    numero: int
    mimo_id: int
    nome_convidado: str
    whatsapp: str
    autoriza_nome_publico: bool
    forma_presente: str
    forma_mimo: str
    preco_presente_reserva: float
    preco_mimo_reserva: float
    valor_pix_total: float
    status: str
    criada_em: datetime
    expira_em: datetime
    confirmada_em: Optional[datetime] = None
    presente_nome: str
    mimo_nome: str
    comprovantes: List[ComprovanteAdminResponse] = []
    pode_confirmar: bool
    horas_restantes: float

    class Config:
        from_attributes = True


class ComprovanteActionRequest(BaseModel):
    status: str  # 'aprovado' ou 'rejeitado'
    observacao: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ["aprovado", "rejeitado", "recebido", "aguardando_envio"]:
            raise ValueError("Status inválido para o comprovante")
        return v


class EstenderPrazoRequest(BaseModel):
    horas_adicionais: int = Field(..., ge=1, le=720)


class DashboardStatsResponse(BaseModel):
    total_numeros: int
    numeros_disponiveis: int
    numeros_reservados: int
    numeros_confirmados: int
    reservas_expiradas: int
    comprovantes_pendentes: int
    valor_total_pix_confirmado: float
    valor_total_pix_pendente: float
    top_presentes: List[Dict[str, Any]]
    top_mimos: List[Dict[str, Any]]


class ProdutoPrincipalCreateUpdate(BaseModel):
    asin: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    imagem_url: Optional[str] = None
    produto_url: Optional[str] = None
    categoria: Optional[str] = None
    preco_atual: float
    preco_anterior: Optional[float] = None
    quantidade_desejada: int = 1
    quantidade_comprada_externa: int = 0
    ativo: bool = True


class MimoCreateUpdate(BaseModel):
    asin: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    imagem_url: Optional[str] = None
    produto_url: Optional[str] = None
    categoria: Optional[str] = None
    preco_atual: float
    preco_anterior: Optional[float] = None
    quantidade_desejada: int = 1
    quantidade_comprada_externa: int = 0
    ativo: bool = True


class ConfiguracaoBulkUpdate(BaseModel):
    configuracoes: Dict[str, str]


class HistoricoAdminResponse(BaseModel):
    id: int
    administrador_nome: Optional[str] = None
    reserva_id: Optional[int] = None
    acao: str
    descricao: str
    criado_em: datetime

    class Config:
        from_attributes = True
