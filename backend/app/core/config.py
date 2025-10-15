import secrets
import warnings
from typing import Annotated, Any, Literal
from sqlalchemy.engine.url import URL  # new import

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"


    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]


    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    MSSQL_SERVER: str
    MSSQL_PORT: int = 1433
    MSSQL_USER: str
    MSSQL_SA_PASSWORD: str = ""
    MSSQL_DB: str = ""

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Dynamically build a SQLAlchemy connection string for MSSQL.
        - Azure SQL: TrustServerCertificate=no
        - Local Docker MSSQL: TrustServerCertificate=yes
        """
        if not self.MSSQL_USER:
            raise ValueError("No MSSQL credentials provided!")

        # Decide whether to trust the server certificate
        if "localhost" in self.MSSQL_SERVER or "mssql" in self.MSSQL_SERVER:
            trust_cert = "yes"
        else:
            trust_cert = "no"

        return (
            "mssql+pyodbc://{user}:{password}@{server}:{port}/{db}"
            "?driver=ODBC+Driver+18+for+SQL+Server"
            "&Encrypt=yes"
            "&TrustServerCertificate={trust_cert}"
            "&ConnectionTimeout=30"
        ).format(
            user=self.MSSQL_USER,
            password=self.MSSQL_SA_PASSWORD,
            server=self.MSSQL_SERVER,
            port=self.MSSQL_PORT,
            db=self.MSSQL_DB,
            trust_cert=trust_cert,
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None



    # Azure
    CLIENT_ID: str = ''
    TENANT_ID: str = ''
    CLIENT_SECRET: str = ''
    # Email
    MAIL_USER: str = ''
    GRAPH_API: str = ''
    # SharePoint
    SITE_DOMAIN: str = ''
    SITE_NAME: str = ''
    SHAREPOINT_FILE_NAME: str = ''
    SHAREPOINT_FOLDER_NAME: str = "Depot Master"

    DEPOT_MASTER: str = ''
    GATE_OUT: str = ''
    DEPOT_ADDRESS: str = ''

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("MSSQL_SA_PASSWORD", self.MSSQL_SA_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self




settings = Settings()  # type: ignore
