import json
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.security.auth import decode_token
from app.models.models import Usuario
from app.services.services import processar_morangia


class MorangIAConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)


manager = MorangIAConnectionManager()


async def websocket_morangia(websocket: WebSocket, token: str = ""):
    await manager.connect(websocket)
    db = SessionLocal()
    try:
        if not token:
            await websocket.send_json({"tipo": "erro", "mensagem": "Token necessário"})
            return
        payload = decode_token(token)
        user = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
        if not user:
            await websocket.send_json({"tipo": "erro", "mensagem": "Usuário inválido"})
            return

        await websocket.send_json({
            "tipo": "sistema",
            "mensagem": f"MorangIA conectada. Olá, {user.nome_completo.split()[0]}!",
            "sugestoes": ["Estoque baixo", "Produtos vencendo", "Movimentações de hoje"],
        })

        while True:
            data = await websocket.receive_json()
            msg = data.get("mensagem", "")
            await websocket.send_json({"tipo": "loading", "mensagem": "MorangIA pensando..."})
            resposta, sugestoes = processar_morangia(db, msg, user)
            await websocket.send_json({"tipo": "resposta", "mensagem": resposta, "sugestoes": sugestoes})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        db.close()
