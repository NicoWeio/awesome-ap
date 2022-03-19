from pathlib import PosixPath


class CoolPath(PosixPath):
    """
    Merkt sich das `cwd`, um `__str__` so zu implementieren, dass nur der Teil-Pfad von Interesse ausgegeben wird.
    """

    def __init__(self, *args, cwd=None):
        super().__init__()
        self.mycwd = cwd
        self.full_path = PosixPath(self)  # TODO: nur ein Workaround

    def __str__(self):
        # Wir können unsere eigene __str__-Methode ja hier nicht verwenden.
        # Aber anstatt die Implementierung der Eltern-Klasse abzuschreiben
        # können wir sie aufrufen, indem wir den Pfad als Instanz der Eltern-Klasse stringifizieren.
        return str(PosixPath(self.relative_to(self.mycwd)))
