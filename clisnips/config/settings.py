from pydantic import BaseModel, ConfigDict, Field

from .palette import Palette, default_palette
from .paths import get_data_path


class AppSettings(BaseModel):
    model_config = ConfigDict(title='Clisnips configuration settings.')
    database: str = Field(
        title='Path to the snippets SQLite database',
        default_factory=lambda: str(get_data_path('snippets.sqlite')),
    )
    palette: Palette = Field(  # type: ignore
        title='The application color palette',
        default_factory=lambda: Palette(**default_palette),
        json_schema_extra={'default': {}},
    )
