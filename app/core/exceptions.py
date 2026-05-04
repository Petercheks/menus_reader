class MenuReaderError(Exception):
    pass


class InvalidImageError(MenuReaderError):
    pass


class ProviderNotConfiguredError(MenuReaderError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"El proveedor '{provider}' no tiene API key configurada")
        self.provider = provider


class UnknownProviderError(MenuReaderError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Proveedor desconocido: '{provider}'")
        self.provider = provider


class ProviderCallError(MenuReaderError):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(f"Error invocando al proveedor '{provider}': {message}")
        self.provider = provider


class InvalidExtractionResultError(MenuReaderError):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(
            f"Resultado del proveedor '{provider}' no valida contra el esquema esperado: {message}"
        )
        self.provider = provider
