"""ABySS native fallback is limited to provable missing mate-distance input."""
import gzip
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from micall.core.assembler_abyss_unlinked import recover
from micall.core.assembler_dispatch import run_external_assembler
from micall.utils.work_dir import WorkDir


class NativeUnlinkedAbyssTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scratch = self.root/"scratch"
        self.work = self.scratch/"assembly_work"
        self.work.mkdir(parents=True)
        (self.work/"assembly-3.fa").write_text(
            ">1 4400 500\nACGTACGTACGT\n>2 4120 200\nTTTTCGAGGGAA\n")
        self.log = self.work/"assembler.log"
        self.log.write_text("DistanceEst: Assertion 'in' failed.\n")

    def mapped(self, alignment=False):
        content = "@HD\tVN:1.4\n@SQ\tSN:1\tLN:4400\n"
        if alignment:
            content += "read1\t0\t1\t1\t40\t12M\t*\t0\t0\tACGTACGTACGT\tIIIIIIIIIIII\n"
        with gzip.open(self.work/"assembly-3.sam.gz", "wt") as writer:
            writer.write(content)

    def test_header_only_reuses_native_unitigs_and_records_identity(self):
        self.mapped()
        target=self.work/"assembly-contigs.fa"
        with self.log.open("ab") as log:
            self.assertTrue(recover(self.work,target,
                                    subprocess.CalledProcessError(2,["abyss-pe"]),log))
        self.assertEqual(target.read_bytes(),(self.work/"assembly-3.fa").read_bytes())
        report=self.root/"assembler_fallback.json"
        self.assertIn('"original_abyss_exit_code": 2',report.read_text())
        self.assertIn("ABYSS_NATIVE_NO_PAIRED_DISTANCE",self.log.read_text())

    def test_one_aligned_mate_cannot_be_silenced(self):
        self.mapped(alignment=True)
        with self.log.open("ab") as log:
            self.assertFalse(recover(self.work,self.work/"assembly-contigs.fa",
                                     subprocess.CalledProcessError(2,["abyss-pe"]),log))
        self.assertFalse((self.work/"assembly-contigs.fa").exists())

    def test_non_distance_or_other_exit_fails_closed(self):
        self.mapped()
        with self.log.open("ab") as log:
            self.assertFalse(recover(self.work,self.work/"assembly-contigs.fa",
                                     subprocess.CalledProcessError(8,["abyss-pe"]),log))
        self.log.write_text("An unrelated assembler failure.")
        with self.log.open("ab") as log:
            self.assertFalse(recover(self.work,self.work/"assembly-contigs.fa",
                                     subprocess.CalledProcessError(2,["abyss-pe"]),log))

    def test_only_abyss_dispatch_uses_no_link_fallback(self):
        from unittest.mock import patch
        left,right=self.root/"R1.fastq",self.root/"R2.fastq"
        left.write_text("@a\nACGT\n+\nIIII\n")
        right.write_text("@a\nACGT\n+\nIIII\n")
        def fake_native(argv, **kw):
            work=kw["cwd"]
            (work/"assembly-3.fa").write_text(
                ">1 4400 500\nACGTACGTACGT\n>2 4120 200\nTTTTCGAGGGAA\n")
            with gzip.open(work/"assembly-3.sam.gz","wt") as stream:
                stream.write("@HD\tVN:1.4\n@SQ\tSN:1\tLN:4400\n")
            kw["stdout"].write(b"DistanceEst: Assertion 'in' failed.\n")
            raise subprocess.CalledProcessError(2,argv)
        with WorkDir.using(self.scratch):
            with patch("micall.core.assembler_dispatch.subprocess.run",
                       side_effect=fake_native):
                output=run_external_assembler("abyss",left,right)
        self.assertIn(">1",output.read_text())
        self.assertIn("NATIVE_GRAPH_UNITIGS_NO_PAIRED_DISTANCE",
                      (self.root/"assembler_fallback.json").read_text())

    def test_non_abyss_failure_never_becomes_a_fallback(self):
        from unittest.mock import patch
        with WorkDir.using(self.scratch):
            with patch("micall.core.assembler_dispatch.subprocess.run",
                       side_effect=subprocess.CalledProcessError(2,["megahit"])):
                with self.assertRaises(subprocess.CalledProcessError):
                    run_external_assembler("megahit",self.root/"R1",self.root/"R2")

    def test_missing_graph_or_broken_gzip_rejected(self):
        self.mapped()
        (self.work/"assembly-3.fa").unlink()
        with self.log.open("ab") as log:
            self.assertFalse(recover(self.work,self.work/"assembly-contigs.fa",
                                     subprocess.CalledProcessError(2,["abyss-pe"]),log))
        (self.work/"assembly-3.fa").write_text(">contig\nACGT\n")
        (self.work/"assembly-3.sam.gz").write_bytes(b"not compressed SAM")
        with self.log.open("ab") as log:
            self.assertFalse(recover(self.work,self.work/"assembly-contigs.fa",
                                     subprocess.CalledProcessError(2,["abyss-pe"]),log))


if __name__=="__main__":
    unittest.main()
