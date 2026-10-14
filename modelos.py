from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Concepto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    termino: str = Field(description="Término importante que aparece en el apunte.")
    explicacion: str = Field(description="Explicación clara y breve del término.")


class Tarjeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pregunta: str = Field(description="Pregunta breve para repasar un contenido del apunte.")
    respuesta: str = Field(description="Respuesta correcta y directa a la pregunta.")


class Pregunta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enunciado: str = Field(description="Enunciado claro de una pregunta de examen.")
    opciones: list[str] = Field(description="Opciones de respuesta para la pregunta.")
    correcta: int = Field(description="Índice, empezando en 0, de la opción correcta dentro de opciones.")

    @field_validator("opciones")
    @classmethod
    def validar_opciones(cls, opciones: list[str]) -> list[str]:
        if len(opciones) != 4:
            raise ValueError(f"La pregunta debe tener exactamente 4 opciones; se recibieron {len(opciones)}.")

        opciones_normalizadas = [opcion.casefold() for opcion in opciones]
        if len(set(opciones_normalizadas)) != 4:
            raise ValueError("Las 4 opciones deben ser distintas entre sí, sin diferencias de mayúsculas o minúsculas.")

        return opciones

    @model_validator(mode="after")
    def validar_indice_correcto(self) -> "Pregunta":
        if not 0 <= self.correcta < len(self.opciones):
            raise ValueError(
                f"El índice correcta debe estar entre 0 y 3 para las cuatro opciones; se recibió {self.correcta}."
            )
        return self


class Apunte(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(description="Título breve que identifica el tema principal del apunte.")
    materia: str = Field(description="Nombre de la materia a la que pertenece el apunte.")
    resumen: str = Field(description="Resumen claro de las ideas principales del apunte.")
    conceptos: list[Concepto] = Field(description="Conceptos importantes del apunte con sus explicaciones.")
    tarjetas: list[Tarjeta] = Field(description="Tarjetas de pregunta y respuesta para repasar el apunte.")
    examen: list[Pregunta] = Field(description="Preguntas de opción múltiple basadas en el contenido del apunte.")
    dificultad: int = Field(description="Nivel de dificultad del apunte, expresado como número entero.")

    @field_validator("dificultad")
    @classmethod
    def validar_dificultad(cls, dificultad: int) -> int:
        if not 1 <= dificultad <= 5:
            raise ValueError(f"La dificultad debe estar entre 1 y 5; se recibió {dificultad}.")
        return dificultad

    @field_validator("conceptos")
    @classmethod
    def validar_cantidad_conceptos(cls, conceptos: list[Concepto]) -> list[Concepto]:
        if len(conceptos) < 3:
            raise ValueError(f"El apunte debe incluir al menos 3 conceptos; se recibieron {len(conceptos)}.")
        return conceptos

    @field_validator("tarjetas")
    @classmethod
    def validar_cantidad_tarjetas(cls, tarjetas: list[Tarjeta]) -> list[Tarjeta]:
        if len(tarjetas) < 5:
            raise ValueError(f"El apunte debe incluir al menos 5 tarjetas; se recibieron {len(tarjetas)}.")
        return tarjetas

    @field_validator("examen")
    @classmethod
    def validar_cantidad_preguntas(cls, examen: list[Pregunta]) -> list[Pregunta]:
        if len(examen) < 3:
            raise ValueError(f"El apunte debe incluir al menos 3 preguntas de examen; se recibieron {len(examen)}.")
        return examen