#!/usr/bin/env python3
"""Optional step for .vcf input

Convert .vcf to a format compatible with Bambino

'indel_vcf_preprocessor' is the main routine of this module
"""

import sys
import pysam
import logging
import pandas as pd
from functools import partial
from .indel_preprocessor import flag_coding_indels
from .indel_snp_annotator import right_trim
from .indel_snp_annotator import count_padding_bases
from .indel_preprocessor import is_chr_prefixed
from .indel_preprocessor import is_canonical_chromosome
from .indel_postprocessor import generate_lt_aln_indel
from .indel_postprocessor import left_align_report

logger = logging.getLogger(__name__)


def indel_vcf_preprocessor(vcffile, bam, refgene, fasta):
    """Convert input VCF to Bambino format and check chromosome name format
    
    Args:
        vcffile (str): path to input vcf
        bam (str): path to bam
        refgene (str): path to refCodingExon.bed.gz
        fasta (str): path to fasta
    Returns:
        df (pandas.DataFrame): df with indels reported as in Bambino output
    """
    vcf_data = open(vcffile)
    df = pd.DataFrame(make_data_list(vcf_data))
    vcf_data.close()

    datasize = len(df)
    if len(df) == 0:
        logging.warning("No indels detected in input vcf. Analysis done.")
        sys.exit(0)

    chr_prefixed = is_chr_prefixed(pysam.AlignmentFile(bam))

    # left-alignment
    df["is_ins"] = df.apply(lambda x: 1 if x["ref"] == "-" else 0, axis=1)
    df["indel_seq"] = df.apply(
        lambda x: x["alt"] if x["ref"] == "-" else x["ref"], axis=1
    )
    lt_aln_indel_generator = partial(
        generate_lt_aln_indel, fa=pysam.FastaFile(fasta), chr_prefixed=chr_prefixed
    )
    df["lt"] = df.apply(lt_aln_indel_generator, axis=1)
    df["pos"], df["ref"], df["alt"] = zip(*df.apply(left_align_report, axis=1))
    df.drop(["lt", "is_ins", "indel_seq"], axis=1, inplace=True)

    coding = partial(
        flag_coding_indels,
        exon_data=pysam.TabixFile(refgene),
        fasta=fasta,
        chr_prefixed=chr_prefixed,
    )
    df["is_coding"] = df.apply(coding, axis=1)
    df = df[df["is_coding"] == True]

    if len(df) == 0:
        logging.warning("No coding indels annotated. Analysis done.")
        sys.exit(0)

    df.drop("is_coding", axis=1, inplace=True)
    df = df.reset_index(drop=True)

    return df, chr_prefixed


def make_data_list(vcf_data):
    """
    Args:
        vcf_data (File obj.): VCF content 
    Returns:
        data (list): with dict element 
    """
    data = []
    for line in vcf_data:
        parsed_line_lst = parse_vcf_line(line)
        if parsed_line_lst:
            for parsed_line in parsed_line_lst:
                d = {
                    "chr": parsed_line[0],
                    "pos": parsed_line[1],
                    "ref": parsed_line[2],
                    "alt": parsed_line[3],
                }

                data.append(d)

    return data


def parse_vcf_line(line):
    """
    Args:
        line (str): line in VCF file obj.
    Returns:
        parsed_line_lst (lst): with tuple elem (chr, pos, ref, alt)
    Example:
      deletion
              pos 123456789012
        reference ATTAGTAGATGT
        deletion  ATTA---GATGT
         
        VCF:
            CHROM POS REF  ALT
            N     4   AGTA A
        Bambino:
            chr   pos ref alt
            chr_N 5   GTA -
         
      insertion
           pos 1234***56789012
        reference ATTA***GTAGATGT
        insertion ATTAGTAGTAGATGT
         
        VCF:
            CHROM POS REF ALT
            N     4   A   AGTA
        Bambino:
            chr   pos ref alt
            chr_N 5   -   GTA   
    """
    parsed_line_lst = []

    # skip header lines
    if line.startswith("#"):
        return parsed_line_lst

    lst = line.rstrip().split("\t")
    chr = lst[0]
    vcf_pos = int(lst[1])
    vcf_ref = lst[3]
    vcf_alts = lst[4].split(",")  # possibly multi-allelic

    if not chr.startswith("chr"):
        chr = "chr" + chr

    # skip non canonical chrmosomes
    if not is_canonical_chromosome(chr):
        return parsed_line_lst

    for vcf_alt in vcf_alts:
        trimmed_ref, trimmed_alt = right_trim(vcf_ref, vcf_alt)
        n = count_padding_bases(trimmed_ref, trimmed_alt)
        pos = vcf_pos + n

        if len(trimmed_ref) < len(trimmed_alt):
            ref = "-"
            alt = trimmed_alt[n:]
            parsed_line_lst.append((chr, pos, ref, alt))
        elif len(trimmed_ref) > len(trimmed_alt):
            ref = trimmed_ref[n:]
            alt = "-"
            parsed_line_lst.append((chr, pos, ref, alt))
        else:
            pass  # not indel

    return parsed_line_lst
