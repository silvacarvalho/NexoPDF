"""Seletor de páginas por arrastar-e-soltar (miniaturas -> caixa de seleção).

Componente Streamlit próprio, em HTML/JS puro (sem build step).
"""

import os

import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
_component_func = components.declare_component("page_picker", path=_FRONTEND_DIR)


def page_picker(pages, key=None):
    """Renderiza uma grade de miniaturas de páginas e uma caixa de seleção
    para onde o usuário arrasta as páginas que deseja extrair.

    Parameters
    ----------
    pages : list[dict]
        Cada item precisa ter: "index" (int, 0-based), "label" (str) e
        "thumb" (str, data URI da miniatura em PNG).
    key : str or None
        Identificador único da instância do componente. Use uma chave que
        mude quando o arquivo enviado mudar, para reiniciar a seleção.

    Returns
    -------
    list[int]
        Índices (0-based) das páginas atualmente na caixa de seleção, na
        ordem em que devem ser exportadas. Pode conter repetições.
    """
    return _component_func(pages=pages, key=key, default=[])
