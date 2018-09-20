from setuptools import setup, find_packages

setup(name='RNAIndel',
      version='0.1',
      description='Somatic Indel Detector for Tumor RNA-Seq Data',
      url='https://github.com/adamdingliang/RNAIndel',
      author='Kohei Hagiwara, Liang Ding',
      author_email='kohei.hagiwara@stjude.org, liang.ding@stjude.org',
      license='Apache License 2.0',
      install_requires=['pandas >= 0.22.0',
                        'numpy >= 1.12.0',
                        'scikit-learn >= 0.18',
                        'pysam == 0.13',
                        'pyvcf == 0.6.8'],
      python_requires='>=3.5.2',
      packages=find_packages('RNAIndel'),
      package_dir={'': 'RNAIndel'},
      package_data={'RNAIndel': ['clnvr/clinvar.indel.old.vcf.gz',
                                 'clnvr/clinvar.indel.old.vcf.gz.tbi',
                                 'clnvr/clinvar.indel.vcf.gz',
                                 'clinvar.indel.vcf.gz.tbi',
                                 'modules/*.pkl.gz',
                                 'refgene/refCodingExon.bed.gz',
                                 'refgene/refCodingExon.bed.gz.tbi',
                                 'testdata/inputs/bambino_sample.txt',
                                 'testdata/outputs/rna_indels.txt']},
      test_suite='tests',
      entry_points={'console_scripts': ['rna_indel = rna_indel:main']}
      )
