from dataclasses import dataclass


@dataclass
class Bucket:
    def has_file(self, id):
        pass

    def get_file(self, id):
        pass

    @property
    def name(self):
        pass