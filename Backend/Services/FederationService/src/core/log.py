import logging

from src.core.environment import EnvHandler


class LoggerHandler:
    def __init__(self, env: EnvHandler) -> None:
        self.env = env
        self._configured = False

        self._appLogger: logging.Logger | None = None
        self._dbLogger: logging.Logger | None = None
        self._security_logger: logging.Logger | None = None
        self._routingLogger: logging.Logger | None = None

    def initialize(self) -> None:
        """
        Configure logging once during application startup.
        """
        if self._configured:
            return

        logLevel = self._parseLogLevel(self.env.LOG_LEVEL)

        logging.basicConfig(
            level=logLevel,
            format=self.env.LOG_FORMAT,
            datefmt=self.env.LOG_DATE_FORMAT,
        )

        self._appLogger = logging.getLogger(self.env.APP_LOGGER_NAME)
        self._dbLogger = logging.getLogger(self.env.DB_LOGGER_NAME)
        self._routingLogger = logging.getLogger(self.env.ROUTING_LOGGER_NAME)

        self._configured = True

    def _parseLogLevel(self, level: str) -> int:
        value = getattr(logging, level.upper(), None)

        if not isinstance(value, int):
            raise ValueError(f"Invalid log level: {level}")

        return value

    def _ensureInitialized(self) -> None:
        if not self._configured:
            raise RuntimeError("LoggerHandler has not been initialized")

    @property
    def app(self) -> logging.Logger:
        self._ensureInitialized()
        assert self._appLogger is not None
        return self._appLogger

    @property
    def database(self) -> logging.Logger:
        self._ensureInitialized()
        assert self._dbLogger is not None
        return self._dbLogger

    @property
    def routing(self) -> logging.Logger:
        self._ensureInitialized()
        assert self._routingLogger is not None
        return self._routingLogger

    def get(self, name: str) -> logging.Logger:
        """
        Optional generic logger accessor.
        Useful for service-specific loggers.
        """
        self._ensureInitialized()
        return logging.getLogger(name)
