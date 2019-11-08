"""
Diff code extracted from meld
(©) 2009 Piotr Piastucki <the_leech@users.berlios.de>
License: GPLv2
"""
from .myers import DiffChunk, MyersSequenceMatcher
from .inline_myers import InlineMyersSequenceMatcher
from .sync_point_myers import SyncPointMyersSequenceMatcher
