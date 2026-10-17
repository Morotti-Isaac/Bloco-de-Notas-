import asyncio
from pathlib import Path

import flet as ft


FUNDO = "#000000"
CARTAO = "#121212"
BOTAO = "#1F1F24"
DESTAQUE = "#7C4DFF"
TEXTO = "#FFFFFF"
TEXTO_SUAVE = "#9A9AA5"


async def main(page: ft.Page):
    page.title = "Bloco de Notas"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = FUNDO
    page.padding = 0
    try: 
        page.window.width = 420
        page.window.height = 800
    except Exception:
        pass

    plataforma = str(page.platform).lower()
    mobile = "android" in plataforma or "ios" in plataforma

    estado = {"arquivo": None, "alterado": False}

    seletor = ft.FilePicker()
    page.services.append(seletor)

    
    titulo = ft.Text("Sem título", size=20, weight=ft.FontWeight.BOLD, color=TEXTO)
    status = ft.Text("Pronto", size=12, color=TEXTO_SUAVE)

    texto = ft.TextField(
        multiline=True,
        expand=True,
        min_lines=10,
        text_size=16,
        color=TEXTO,
        bgcolor=CARTAO,
        border_color=BOTAO,
        focused_border_color=DESTAQUE,
        cursor_color=DESTAQUE,
        border_radius=16,
        content_padding=16,
        hint_text="Escreva sua nota aqui...",
        hint_style=ft.TextStyle(color=TEXTO_SUAVE),
    )

    def atualizar_titulo():
        nome = Path(estado["arquivo"]).name if estado["arquivo"] else "Sem título"
        titulo.value = nome + (" *" if estado["alterado"] else "")
        page.update()

    def ao_digitar(e):
        if not estado["alterado"]:
            estado["alterado"] = True
            atualizar_titulo()

    texto.on_change = ao_digitar

    def mostrar_status(msg):
        status.value = msg
        page.update()

    
    cartao_modal = ft.Container(bgcolor=CARTAO, border_radius=24, padding=24, width=320)
    camada = ft.Container(
        visible=False,
        expand=True,
        bgcolor="#CC000000",
        alignment=ft.Alignment(0, 0),
        content=cartao_modal,
    )

    def botao(rotulo, icone, ao_clicar, principal=False):
        return ft.Button(
            content=rotulo,
            icon=icone,
            on_click=ao_clicar,
            style=ft.ButtonStyle(
                bgcolor=DESTAQUE if principal else BOTAO,
                color=TEXTO,
                icon_color=TEXTO,
                shape=ft.RoundedRectangleBorder(radius=14),
                padding=14,
            ),
        )

    def fechar_modal():
        camada.visible = False
        page.update()

    async def perguntar_salvar():
        """Mostra 'Salvar / Não salvar / Cancelar'. Devolve 'sim', 'nao' ou 'cancelar'."""
        resposta = asyncio.get_running_loop().create_future()

        def responder(valor):
            def _(e):
                if not resposta.done():
                    resposta.set_result(valor)
            return _

        cartao_modal.content = ft.Column(
            tight=True,
            spacing=14,
            controls=[
                ft.Text("Alterações não salvas", size=18, weight=ft.FontWeight.BOLD, color=TEXTO),
                ft.Text("Deseja salvar as alterações antes de continuar?", color=TEXTO_SUAVE),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        botao("Salvar", ft.Icons.SAVE, responder("sim"), principal=True),
                        botao("Descartar", ft.Icons.DELETE_OUTLINE, responder("nao")),
                        botao("Cancelar", ft.Icons.CLOSE, responder("cancelar")),
                    ],
                ),
            ],
        )
        camada.visible = True
        page.update()
        valor = await resposta
        fechar_modal()
        return valor

    async def confirmar_descarte() -> bool:
        if not estado["alterado"]:
            return True
        valor = await perguntar_salvar()
        if valor == "cancelar":
            return False
        if valor == "sim":
            return await salvar()
        return True

    async def novo(e=None):
        if not await confirmar_descarte():
            return
        texto.value = ""
        estado["arquivo"] = None
        estado["alterado"] = False
        atualizar_titulo()
        mostrar_status("Nova nota")

    async def abrir(e=None):
        if not await confirmar_descarte():
            return
        try:
            arquivos = await seletor.pick_files(allow_multiple=False)
            if not arquivos:
                return
            caminho = arquivos[0].path
            conteudo = Path(caminho).read_text(encoding="utf-8")
        except (OSError, UnicodeError, TypeError) as erro:
            mostrar_status(f"Erro ao abrir: {erro}")
            return
        texto.value = conteudo
        estado["arquivo"] = caminho
        estado["alterado"] = False
        atualizar_titulo()
        mostrar_status("Arquivo aberto")

    async def salvar_como(e=None) -> bool:
        nome = Path(estado["arquivo"]).name if estado["arquivo"] else "nota.txt"
        try:
            if mobile:
                destino = await seletor.save_file(
                    dialog_title="Salvar nota",
                    file_name=nome,
                    allowed_extensions=["txt"],
                    src_bytes=texto.value.encode("utf-8"),
                )
            else:
                destino = await seletor.save_file(
                    dialog_title="Salvar nota",
                    file_name=nome,
                    allowed_extensions=["txt"],
                )
                if destino:
                    if not Path(destino).suffix:
                        destino += ".txt"
                    Path(destino).write_text(texto.value, encoding="utf-8")
        except Exception as erro:
            mostrar_status(f"Erro ao salvar: {erro}")
            return False
        if not destino:
            return False  # o usuário cancelou
        estado["arquivo"] = destino
        estado["alterado"] = False
        atualizar_titulo()
        mostrar_status("Nota salva")
        return True

    async def salvar(e=None) -> bool:
        # No Android, arquivos abertos são cópias temporárias; por isso salva sempre pelo seletor.
        if mobile or estado["arquivo"] is None:
            return await salvar_como()
        try:
            Path(estado["arquivo"]).write_text(texto.value, encoding="utf-8")
        except OSError as erro:
            mostrar_status(f"Erro ao salvar: {erro}")
            return False
        estado["alterado"] = False
        atualizar_titulo()
        mostrar_status("Nota salva")
        return True

    def abrir_creditos(e=None):
        cartao_modal.content = ft.Column(
            tight=True,
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Créditos", size=18, weight=ft.FontWeight.BOLD, color=TEXTO),
                ft.Container(
                    content=ft.Image(src="foto.png", width=180, height=180),
                    width=180,
                    height=180,
                    border_radius=90,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),
                ft.Text("Isaac Morotti", size=22, weight=ft.FontWeight.BOLD, color=TEXTO),
                botao("Fechar", ft.Icons.CLOSE, lambda _: fechar_modal(), principal=True),
            ],
        )
        camada.visible = True
        page.update()

    cabecalho = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Column(
                spacing=0,
                expand=True,
                controls=[ft.Text("BLOCO DE NOTAS", size=11, color=DESTAQUE, weight=ft.FontWeight.BOLD), titulo],
            ),
            botao("Créditos", ft.Icons.INFO_OUTLINE, abrir_creditos),
        ],
    )

    barra = ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            botao("Novo", ft.Icons.NOTE_ADD_OUTLINED, novo),
            botao("Abrir", ft.Icons.FOLDER_OPEN, abrir),
            botao("Salvar", ft.Icons.SAVE, salvar, principal=True),
            botao("Salvar como", ft.Icons.SAVE_AS, salvar_como),
        ],
    )

    principal = ft.Column(
        expand=True,
        spacing=14,
        controls=[cabecalho, barra, texto, status],
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Container(content=principal, padding=16, expand=True),
                    camada,
                ],
            ),
        )
    )


if hasattr(ft, "run"):
    ft.run(main, assets_dir="assets")
else:
    ft.app(target=main, assets_dir="assets")
