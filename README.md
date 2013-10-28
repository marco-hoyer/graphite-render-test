graphite-render-test
====================

Some tools for automated testing of the graphite render API

### load testing with random data
- take 20 random targets
- request them for 10 times each
- wait 0.1 s between each iteration

python graphite-render-test.py <host> --targetfile graphite_index.txt --checknones --interval 0.1 --count 10 --numberoftargets 20
