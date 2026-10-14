import streamlit as st

from cerebro import ImagenIlegible, analizar_pagina, calificar, crear_cliente


st.set_page_config(page_title="Mi cuaderno habla", page_icon="📓", layout="centered")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error(
        "No encontré GEMINI_API_KEY. Agregala en .streamlit/secrets.toml con el formato "
        'GEMINI_API_KEY = "tu_llave" y volvé a iniciar la aplicación.'
    )
    st.stop()

# Streamlit vuelve a ejecutar este archivo después de cada interacción; el estado conserva los datos entre ejecuciones.
if "apunte" not in st.session_state:
    st.session_state.apunte = None
if "respuestas_examen" not in st.session_state:
    st.session_state.respuestas_examen = {}
if "examen_entregado" not in st.session_state:
    st.session_state.examen_entregado = False
if "puntaje" not in st.session_state:
    st.session_state.puntaje = None


st.title("Mi cuaderno habla")
st.write("Tomá una foto o subí la página de tu cuaderno para crear una guía de estudio.")

tab_foto, tab_subir = st.tabs(["Tomar foto", "Subir imagen"])
with tab_foto:
    imagen_camara = st.camera_input("Fotografiá la página")
with tab_subir:
    imagen_archivo = st.file_uploader(
        "Elegí una imagen de la página",
        type=["png", "jpg", "jpeg", "webp"],
    )

imagen = imagen_archivo if imagen_archivo is not None else imagen_camara

if st.button("Analizar la página", type="primary"):
    if imagen is None:
        st.error("Tomá una foto o subí una imagen antes de analizar la página.")
    else:
        try:
            with st.spinner("Analizando la página..."):
                cliente = crear_cliente(api_key)
                apunte_nuevo = analizar_pagina(
                    imagen.getvalue(),
                    imagen.type or "image/jpeg",
                    cliente,
                )

            if st.session_state.apunte is not None:
                for indice in range(len(st.session_state.apunte.examen)):
                    clave = f"respuesta_examen_{indice}"
                    if clave in st.session_state:
                        del st.session_state[clave]

            st.session_state.apunte = apunte_nuevo
            st.session_state.respuestas_examen = {}
            st.session_state.examen_entregado = False
            st.session_state.puntaje = None
        except ImagenIlegible as error:
            st.warning(str(error))
        except Exception:
            st.error("No se pudo analizar la página. Revisá la imagen y la configuración, e intentá de nuevo.")


apunte = st.session_state.apunte
if apunte is not None:
    st.header(apunte.titulo)
    st.write(f"**Materia:** {apunte.materia}")
    st.write(f"**Dificultad:** {'⭐' * apunte.dificultad} ({apunte.dificultad}/5)")

    st.subheader("Resumen")
    st.write(apunte.resumen)

    st.subheader("Conceptos")
    for concepto in apunte.conceptos:
        st.markdown(f"- **{concepto.termino}:** {concepto.explicacion}")

    st.subheader("Tarjetas de repaso")
    for indice, tarjeta in enumerate(apunte.tarjetas):
        with st.expander(tarjeta.pregunta, key=f"tarjeta_{indice}"):
            st.write(tarjeta.respuesta)

    st.subheader("Examen")
    respuestas_actuales = {}
    for indice, pregunta in enumerate(apunte.examen):
        seleccion = st.radio(
            f"{indice + 1}. {pregunta.enunciado}",
            options=list(range(len(pregunta.opciones))),
            format_func=lambda opcion, opciones=pregunta.opciones: opciones[opcion],
            index=None,
            key=f"respuesta_examen_{indice}",
            disabled=st.session_state.examen_entregado,
        )
        if seleccion is not None:
            respuestas_actuales[indice] = seleccion

    st.session_state.respuestas_examen = respuestas_actuales

    if st.button("Entregar examen", disabled=st.session_state.examen_entregado):
        st.session_state.examen_entregado = True
        st.session_state.puntaje = calificar(apunte, st.session_state.respuestas_examen)
        if st.session_state.puntaje[0] == st.session_state.puntaje[1]:
            st.balloons()

    if st.session_state.examen_entregado:
        aciertos, total = st.session_state.puntaje
        st.metric("Puntaje", f"{aciertos} / {total}")
        for indice, pregunta in enumerate(apunte.examen):
            respuesta = st.session_state.respuestas_examen.get(indice)
            if respuesta == pregunta.correcta:
                st.success(f"Pregunta {indice + 1}: correcta.")
            else:
                st.error(
                    f"Pregunta {indice + 1}: incorrecta. "
                    f"La respuesta correcta era: {pregunta.opciones[pregunta.correcta]}"
                )

    guia = [
        f"# {apunte.titulo}",
        f"**Materia:** {apunte.materia}",
        f"**Dificultad:** {apunte.dificultad}/5",
        "",
        "## Resumen",
        apunte.resumen,
        "",
        "## Conceptos",
    ]
    for concepto in apunte.conceptos:
        guia.append(f"- **{concepto.termino}:** {concepto.explicacion}")

    guia.extend(["", "## Tarjetas de repaso"])
    for tarjeta in apunte.tarjetas:
        guia.extend([f"### {tarjeta.pregunta}", tarjeta.respuesta, ""])

    guia.extend(["## Examen"])
    for indice, pregunta in enumerate(apunte.examen):
        guia.append(f"### {indice + 1}. {pregunta.enunciado}")
        guia.extend(f"- {opcion}" for opcion in pregunta.opciones)
        guia.append(f"**Respuesta correcta:** {pregunta.opciones[pregunta.correcta]}")

    st.download_button(
        "Descargar guía de estudio",
        data="\n".join(guia),
        file_name="guia_de_estudio.md",
        mime="text/markdown",
    )