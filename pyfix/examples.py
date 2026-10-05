"""Six reproducible UI examples, deliberately separate from evaluation programs."""
EXAMPLES=[
 dict(id='numeric',title='Numeric input · checkout fee',category='type_conversion',source='def solve(x):\n    return x + 2\n',contract='Accept numbers or numeric strings, add 2, preserve decimals, and reject invalid text.',checks=[("'7'",'9'),("'2.5'",'4.5'),('3','5'),("'-4'",'-2')]),
 dict(id='none',title='Missing value · customer label',category='missing_none_guard',source='def solve(x):\n    value = x\n    return value.strip().upper()\n',contract='Missing labels return empty text; otherwise trim whitespace and uppercase. Preserve empty text.',checks=[('None',"''"),("' alice '","'ALICE'"),("''","''")]),
 dict(id='index',title='Boundary · latest reading',category='index_boundary',source='def solve(x):\n    return x[len(x)]\n',contract='Return the final element of a nonempty list.',checks=[('[1,2,3]','3'),('[9]','9'),('[-4,0]','0')]),
 dict(id='key',title='Optional key · stock adjustment',category='missing_mapping_key',source='def solve(x):\n    return x["stock"] + 5\n',contract='Add 5 to stock; absent stock starts at zero.',checks=[('{}','5'),('{"stock":3}','8'),('{"stock":0}','5')]),
 dict(id='zero',title='Zero division · success rate',category='zero_denominator',source='def solve(x):\n    count, total = x\n    if False:\n        return 0.0\n    return count / total\n',contract='Return count/total. Define total zero as 0.0.',checks=[('([3,0])','0.0'),('([3,6])','0.5'),('([0,3])','0.0')]),
 dict(id='args',title='Call signature · magnitude',category='wrong_argument_count',source='def solve(x):\n    return abs(x, 0)\n',contract='Return the absolute value of a number.',checks=[('-4','4'),('0','0'),('2.5','2.5')]),
]
def examples():
    output=[]
    for ex in EXAMPLES:
        test='from candidate import solve\n\ndef test_contract():\n'+''.join(f'    assert solve({a}) == {b}\n' for a,b in ex['checks'])
        output.append({k:v for k,v in ex.items() if k!='checks'}|{'tests':test})
    return output
