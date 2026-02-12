import os
import tempfile

from attendance import get_students_data


def touch(path):
    with open(path, "wb") as f:
        f.write(b"\x00")


def test_get_students_data_branch_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample image files matching repo naming convention
        # CSE student (branch code '05' expected at rollno[-4:-2])
        cse_fname = "22FE1A0505_John_CSE.jpg"
        aiml_fname = "22FE1A6101_Alice_AIML.jpg"
        other_fname = "INVALID_FILE.txt"

        touch(os.path.join(tmpdir, cse_fname))
        touch(os.path.join(tmpdir, aiml_fname))
        touch(os.path.join(tmpdir, other_fname))

        # No branch filter -> both valid students returned
        all_students = get_students_data(images_path_local=tmpdir, branch_filter=None)
        branches = {s['Branch'] for s in all_students}
        assert 'CSE' in branches and 'AIML' in branches

        # Filter for CSE only
        cse_only = get_students_data(images_path_local=tmpdir, branch_filter='CSE')
        assert len(cse_only) == 1
        assert cse_only[0]['Branch'] == 'CSE'
        # names are uppercased by the loader
        assert cse_only[0]['Name'] == 'JOHN'
