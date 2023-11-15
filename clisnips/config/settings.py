from pydantic import BaseModel, Field

from .paths import get_data_path
from .palette import Palette


class AppSettings(BaseModel):
    database: str = Field(
        title='Path to the snippets SQLite database',
        default_factory=lambda: str(get_data_path('snippets.sqlite')),
    )
    palette: Palette = Field(
        title='The application colors',
        default={},
    )
