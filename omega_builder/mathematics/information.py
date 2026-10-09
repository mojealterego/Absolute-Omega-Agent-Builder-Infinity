"""Discrete information-theory primitives and finite Huffman prefix coding."""
from __future__ import annotations
from collections import Counter
from heapq import heappop,heappush
from itertools import count
from math import fsum, isfinite, log, log10
from .probability import distribution, entropy, ProbabilityError


def _joint(values):
    if not isinstance(values,(list,tuple)) or not 1<=len(values)<=256:
        raise ProbabilityError("Expected nonempty joint probability matrix")
    if not isinstance(values[0],(list,tuple)) or not 1<=len(values[0])<=256:
        raise ProbabilityError("Expected nonempty columns")
    n=len(values[0])
    if any(not isinstance(r,(list,tuple)) or len(r)!=n for r in values):
        raise ProbabilityError("Ragged joint probability")
    flat=[]
    for row in values:
        for v in row:
            if type(v) not in (int,float) or not isfinite(float(v)) or v<0:
                raise ProbabilityError("Joint probability entries must be finite and nonnegative")
            flat.append(float(v))
    if abs(fsum(flat)-1.)>1e-9:
        raise ProbabilityError("Joint distribution must sum to 1")
    return [[float(x) for x in row] for row in values]


def conditional_entropy_y_given_x(joint):
    """H(Y|X); X=row and Y=column of the supplied joint PMF."""
    a=_joint(joint)
    marg=[fsum(row) for row in a]
    return -fsum(v*log(v/p,2) for row,p in zip(a,marg) if p
                 for v in row if v)


def mutual_information(joint):
    """I(X;Y)=sum p(x,y)log2(p(x,y)/(p(x)p(y)))."""
    a=_joint(joint)
    px=[fsum(row) for row in a]
    py=[fsum(row[j] for row in a) for j in range(len(a[0]))]
    value=fsum(v*log(v/(px[i]*py[j]),2)
               for i,row in enumerate(a) for j,v in enumerate(row) if v)
    return max(0.,value) if value > -1e-12 else value


def joint_entropy(joint):
    a=_joint(joint)
    return -fsum(v*log(v,2) for row in a for v in row if v)


def signal_to_noise_db(signal_power,noise_power):
    if type(signal_power) not in (int,float) or type(noise_power) not in (int,float):
        raise ProbabilityError("Power must be numerical")
    signal_power,noise_power=float(signal_power),float(noise_power)
    if not isfinite(signal_power) or not isfinite(noise_power) or signal_power<=0 or noise_power<=0:
        raise ProbabilityError("Positive signal and noise power required")
    return 10*log10(signal_power/noise_power)


def shannon_hartley(bandwidth_hz,snr_linear):
    if type(bandwidth_hz) not in (int,float) or type(snr_linear) not in (int,float):
        raise ProbabilityError("Expected real bandwidth and power ratio")
    bandwidth_hz,snr_linear=float(bandwidth_hz),float(snr_linear)
    if not isfinite(bandwidth_hz) or not isfinite(snr_linear) or bandwidth_hz<0 or snr_linear<0:
        raise ProbabilityError("Expected nonnegative finite arguments")
    return bandwidth_hz*__import__("math").log2(1+snr_linear)


def huffman_codes(symbol_counts):
    """Optimal binary prefix code LENGTH for known finite positive counts.

    Codes generated with deterministic tie resolution; codes must accompany
    the bitstream when used for persistent transmission.
    """
    if not isinstance(symbol_counts,dict) or not 1<=len(symbol_counts)<=1024:
        raise ProbabilityError("Provide 1..1024 symbols")
    if any(not isinstance(k,str) or not k or type(v) is not int or not 1<=v<=10**12
           for k,v in symbol_counts.items()):
        raise ProbabilityError("Symbols must be strings and counts positive integers")
    counter=count()
    heap=[]
    for symbol,weight in sorted(symbol_counts.items()):
        heappush(heap,(weight,next(counter),symbol))
    if len(heap)==1:
        return {heap[0][2]:"0"}
    while len(heap)>1:
        w1,_,a=heappop(heap)
        w2,_,b=heappop(heap)
        heappush(heap,(w1+w2,next(counter),(a,b)))
    tree=heap[0][2]
    result={}
    def walk(node,code):
        if isinstance(node,str):
            result[node]=code
        else:
            walk(node[0],code+"0")
            walk(node[1],code+"1")
    walk(tree,"")
    return result


def huffman_encode(symbols,codes):
    if not isinstance(symbols,(tuple,list)) or len(symbols)>100000:
        raise ProbabilityError("Input symbol list exceeds limit")
    if not isinstance(codes,dict) or not codes:
        raise ProbabilityError("Nonempty codebook required")
    if any(symbol not in codes for symbol in symbols):
        raise ProbabilityError("Unknown symbol")
    return "".join(codes[s] for s in symbols)


def huffman_decode(bits,codes):
    if not isinstance(bits,str) or len(bits)>10000000 or set(bits)-{"0","1"}:
        raise ProbabilityError("Bitstream must be bounded binary string")
    if not isinstance(codes,dict) or not codes:
        raise ProbabilityError("Codebook required")
    inverted={}
    for symbol,code in codes.items():
        if not isinstance(symbol,str) or not isinstance(code,str) or not code or set(code)-{"0","1"}:
            raise ProbabilityError("Invalid prefix code")
        inverted[code]=symbol
    if len(inverted)!=len(codes):
        raise ProbabilityError("Duplicate codeword")
    all_codes=list(inverted)
    if any(a.startswith(b) for a in all_codes for b in all_codes if a!=b):
        raise ProbabilityError("Not prefix-free")
    decoded=[];buf=""
    for bit in bits:
        buf+=bit
        if buf in inverted:
            decoded.append(inverted[buf])
            buf=""
    if buf:
        raise ProbabilityError("Truncated or invalid bitstream")
    return decoded
