These are collection of tests that should be used to stress test alalfa at scale. 

Dependencies

pip install pytest-parallel

Example to execute 

poetry run pytest --workers 40  --tests-per-worker 1  -m "stress" -rP

Right now the test should execute 1 test per worker as I do not beleive these are thread safe. 
one worker is a forked process and provides isolation so do a one to one





