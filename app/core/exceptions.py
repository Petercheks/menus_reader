class MenuReaderError(Exception):
    pass


class InvalidImageError(MenuReaderError):
    pass


class ProviderNotConfiguredError(MenuReaderError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider '{provider}' has no API key configured")
        self.provider = provider


class UnknownProviderError(MenuReaderError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Unknown provider: '{provider}'")
        self.provider = provider


class ProviderCallError(MenuReaderError):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(f"Error calling provider '{provider}': {message}")
        self.provider = provider


class InvalidExtractionResultError(MenuReaderError):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(
            f"Result from provider '{provider}' does not match expected schema: {message}"
        )
        self.provider = provider
