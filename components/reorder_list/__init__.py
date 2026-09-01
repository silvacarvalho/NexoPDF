"""Lista arrastável (drag-and-drop) para reordenar itens.

Componente Streamlit próprio, em HTML/JS puro (sem build step), para evitar
os problemas visuais/comportamentais de bibliotecas de terceiros.
"""

import os

import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
_component_func = components.declare_component("reorder_list", path=_FRONTEND_DIR)


def reorder_list(items, key=None):
    """Renderiza uma lista de cartões que o usuário pode arrastar para reordenar.

    Parameters
    ----------
    items : list[dict]
        Cada item precisa ter uma chave "id" (str, única) e "title" (str).
        Chaves opcionais: "subtitle" (str) e "icon" (str, um emoji).
    key : str or None
        Identificador único da instância do componente.

    Returns
    -------
    list[str]
        Lista de "id"s na ordem atual (após eventuais arrastos do usuário).
    """
    default_order = [item["id"] for item in items]
    return _component_func(items=items, key=key, default=default_order)
