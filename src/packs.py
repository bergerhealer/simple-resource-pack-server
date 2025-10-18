from loguru import logger
from models import PackMetadata, MinecraftVersionRange
from typing import Optional, List
from datetime import datetime, UTC

import uuid
import os
import json


class PackCache:

    def __init__(self, packs_dir):
        self.packs_dir = packs_dir
        self.by_slug = {}
        self.main = []

    def get(self, slug: str) -> Optional[PackMetadata]:
        return self.by_slug.get(slug, None)

    def get_main(self) -> PackMetadata:
        cnt = len(self.main)
        return self.main[cnt - 1]

    def get_main_packs(self) -> List[PackMetadata]:
        return self.main

    def get_next_slug(self) -> str:
        while True:
            slug = uuid.uuid4().hex[:8]
            if slug not in self.by_slug:
                return slug

    def get_zip_path(self, slug) -> str:
        return os.path.join(self.packs_dir, f"{slug}.zip")

    def is_zip_equal(self, slug: str, zip_data: bytes) -> bool:
        path = self.get_zip_path(slug)
        try:
            with open(path, 'rb') as f:
                existing_bytes = f.read()
            return zip_data == existing_bytes
        except:
            logger.exception(f"Error comparing ZIP file: {path}")
            return False

    def save_new_zip(self, meta: PackMetadata, zip_data: bytes, zip_sha1: str) -> PackMetadata:
        new_meta: PackMetadata = meta.copy(update={
            'slug': self.get_next_slug(),
            'uploaded': datetime.now(UTC),
            'sha1': zip_sha1,
            'main': True,
            'is_temporary': False
        })
        new_zip_path = self.get_zip_path(new_meta.slug)
        with open(new_zip_path, "wb") as f:
            f.write(zip_data)

        # Drop temporary metadata if one existed
        # Simply mark it as non-main for other previous metadata
        # This still allows it to be downloaded, but it will not show up in the
        # selection dropdown
        if meta.is_temporary:
            self.by_slug.pop(meta.slug, None)
            self.main = [main_pack for main_pack in self.main if main_pack.slug != meta.slug]
        else:
            self.update(meta.copy(update={
                'main': False
            }))

        self.update(new_meta)
        return new_meta

    def duplicate(self, meta: PackMetadata) -> PackMetadata:
        new_meta: PackMetadata = meta.copy(update={
            'slug': self.get_next_slug(),
            'uploaded': datetime.now(UTC),
            'sha1': '',
            'main': True,
            'is_temporary': True
        })
        self.update(new_meta)
        return new_meta

    def update(self, meta: PackMetadata, save: bool = True):
        self.main = [main_pack for main_pack in self.main if main_pack.slug != meta.slug]
        self.by_slug[meta.slug] = meta
        if meta.main:
            self.main.append(meta)
            self.main = sorted(self.main, key=lambda m: m.minecraft.minimum)

        if save and not meta.is_temporary:
            pack_json_file = os.path.join(self.packs_dir, f"{meta.slug}.json")
            with open(pack_json_file, "w") as f:
                json.dump(meta.model_dump(), f, indent=2, default=str)

    def load(self):
        self.by_slug = {}
        self.main = []
        for fname in os.listdir(self.packs_dir):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(self.packs_dir, fname), "r") as f:
                        self.update(PackMetadata(**json.load(f)), save=False)
                except Exception:
                    logger.exception(f"Error loading {fname}")

        # If there are no mainline packs yet, fake one
        # This is a pack that does not actually exist on disk yet
        if not self.main:
            self.update(PackMetadata(
                name='No Packs Set',
                slug='00000000',
                uploaded=datetime.now(UTC),
                minecraft=MinecraftVersionRange(minimum='1.8', maximum='1.21.10'),
                sha1='',
                main=True,
                is_temporary=True), save=False)
