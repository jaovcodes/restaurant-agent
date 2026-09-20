"""Memória de conversa por sessão, guardada em RAM.

A API da Mistral não guarda estado: a cada chamada precisamos reenviar o
histórico inteiro. Esta classe mantém esse histórico por `session_id`.

Limitação assumida (projeto acadêmico): reiniciar o servidor apaga as conversas.
"""

import threading


class MemoriaSessoes:
    def __init__(self, max_mensagens: int = 40):
        self._max = max_mensagens
        self._sessoes: dict[str, list[dict]] = {}
        # O FastAPI atende requisições em threads diferentes.
        self._lock = threading.Lock()

    def obter(self, session_id: str) -> list[dict]:
        with self._lock:
            return list(self._sessoes.get(session_id, []))

    def adicionar(self, session_id: str, mensagens: list[dict]) -> None:
        with self._lock:
            historico = self._sessoes.setdefault(session_id, [])
            historico.extend(mensagens)
            self._podar(historico)

    def limpar(self, session_id: str) -> None:
        with self._lock:
            self._sessoes.pop(session_id, None)

    def _podar(self, historico: list[dict]) -> None:
        """Descarta as mensagens mais antigas, mas sempre em turnos completos.

        Cortar no meio de um turno deixaria uma mensagem 'tool' sem a chamada
        que a originou, e a API da Mistral rejeita esse histórico. Por isso o
        corte só acontece imediatamente antes de uma mensagem do usuário.
        """
        while len(historico) > self._max:
            proximo_turno = next(
                (i for i in range(1, len(historico)) if historico[i]["role"] == "user"),
                None,
            )
            if proximo_turno is None:
                break
            del historico[:proximo_turno]
