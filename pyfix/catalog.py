"""Authored small programs. A mutation removes/replaces exactly one marked expression.
Fixtures vary real input values. Program identities never cross data partitions.
These are synthetic tasks, not real repository bugs.
"""
from dataclasses import dataclass
import ast

@dataclass(frozen=True)
class Program:
    name: str
    label: str
    body: str
    good: str
    bad: str
    inputs: tuple
    contract: str

    def source(self, broken=False):
        expression = self.bad if broken else self.good
        return ast.unparse(ast.parse(self.body.replace('@', expression)))+'\n'

def p(name,label,body,good,bad,inputs,contract):
    return Program(name,label,body,good,bad,tuple(inputs),contract)

PROGRAMS = []
def add(label, entries):
    PROGRAMS.extend(p(name,label,*rest) for name,*rest in entries)

add('type_conversion', [
 ('invoice_total','def solve(x):\n    subtotal = 0\n    for price in x:\n        subtotal += @\n    return round(subtotal * 1.05, 2)','float(price)','price', [[str(i),str(i+.5)] for i in range(1,9)],'Sum numeric price strings and add 5% tax.'),
 ('temperature','def solve(x):\n    readings = []\n    for reading in x:\n        readings.append((@ - 32) * 5 / 9)\n    return readings','float(reading)','reading',[[str(30+i),str(60+i)] for i in range(8)],'Convert Fahrenheit numeric strings to Celsius, preserving order.'),
 ('shipping','def solve(x):\n    mass = @\n    base = 4\n    return mass + base','float(x)','x',[str(i+.2) for i in range(8)],'Shipping costs 4 plus the numeric weight.'),
 ('savings','def solve(x):\n    amount = @\n    monthly = amount / 12\n    return round(monthly, 2)','float(x)','x',[str(100+i*12) for i in range(8)],'Convert annual numeric-text savings to rounded monthly savings.'),
 ('pace','def solve(x):\n    distance = @\n    seconds = 3600\n    return seconds / distance','float(x)','x',[str(i+1) for i in range(8)],'Return seconds per distance unit for a one-hour numeric-text distance.'),
 ('inventory_value','def solve(x):\n    values = []\n    for quantity in x:\n        values.append(@ * 2.5)\n    return sum(values)','int(quantity)','quantity',[[str(i),str(i+2)] for i in range(8)],'Inventory units are integer strings; each is worth 2.5.'),
 ('sensor_average','def solve(x):\n    total = sum(@ for sample in x)\n    return total / len(x)','float(sample)','sample',[[str(i+.1),str(i+.3)] for i in range(8)],'Average nonempty numeric string readings.'),
 ('duration','def solve(x):\n    hours, minutes = x.split(":")\n    return @ * 60 + int(minutes)','int(hours)','hours',[f'{i}:30' for i in range(8)],'Convert an hours:minutes string into minutes.'),
])
add('missing_none_guard', [
 ('optional_tags','def solve(x):\n    tags = @\n    return [tag.lower() for tag in tags]','x if x is not None else []','x',[None]*8,'Missing tags produce an empty list; otherwise lowercase each tag.'),
 ('display_name','def solve(x):\n    text = @\n    return text.strip().title()','x if x is not None else ""','x',[None]*8,'Missing names produce an empty string; otherwise strip and title-case.'),
 ('optional_scores','def solve(x):\n    scores = @\n    return sum(scores)','x if x is not None else []','x',[None]*8,'Missing scores have sum zero; sum present scores.'),
 ('optional_config','def solve(x):\n    settings = @\n    return settings.get("theme", "light")','x if x is not None else {}','x',[None]*8,'Missing settings use light theme; respect present theme values.'),
 ('optional_comment','def solve(x):\n    comment = @\n    return len(comment.split())','x if x is not None else ""','x',[None]*8,'Count comment words; None means no words.'),
 ('optional_locations','def solve(x):\n    locations = @\n    return sorted(set(locations))','x if x is not None else []','x',[None]*8,'Return unique sorted locations; None means empty.'),
 ('optional_record','def solve(x):\n    record = @\n    return list(record.keys())','x if x is not None else {}','x',[None]*8,'Return mapping keys, or an empty list for None.'),
 ('optional_label','def solve(x):\n    label = @\n    return label.replace("_", " ")','x if x is not None else ""','x',[None]*8,'Replace underscores with spaces; None means empty text.'),
])
add('index_boundary', [
 ('latest_event','def solve(x):\n    events = sorted(x)\n    return events[@]','len(events)-1','len(events)',[[i,i+3,i+1] for i in range(8)],'Return the latest value in a nonempty event list.'),
 ('reverse_queue','def solve(x):\n    output = []\n    for i in range(len(x)):\n        output.append(x[@])\n    return output','len(x)-1-i','len(x)-i',[[i,i+1] for i in range(8)],'Reverse a nonempty list without changing its members.'),
 ('last_character','def solve(x):\n    text = x.strip()\n    return text[@]','len(text)-1','len(text)',[f'item{i}' for i in range(8)],'Return last character after trimming a nonempty string.'),
 ('running_difference','def solve(x):\n    result = []\n    for i in range(@):\n        result.append(x[i+1]-x[i])\n    return result','len(x)-1','len(x)',[[i,i+2,i+5] for i in range(8)],'Return consecutive differences of a numeric sequence.'),
 ('pair_totals','def solve(x):\n    pairs = []\n    for i in range(0, @, 2):\n        pairs.append(x[i]+x[i+1])\n    return pairs','len(x)','len(x)+1',[[i,i+1,i+2,i+3] for i in range(8)],'Sum each consecutive pair in an even-length sequence.'),
 ('middle_window','def solve(x):\n    values = sorted(x)\n    tail = values[1:]\n    return tail[@]','len(tail)-1','len(tail)',[[i,i+2,i+1] for i in range(8)],'Return the largest element after dropping the smallest.'),
 ('suffix','def solve(x):\n    parts = x.split(".")\n    return parts[@]','len(parts)-1','len(parts)',[f'file{i}.txt' for i in range(8)],'Return the last dot-separated filename component.'),
 ('backward_scan','def solve(x):\n    output = []\n    for i in range(1, @):\n        output.append(x[-i])\n    return output','len(x)+1','len(x)+2',[[i,i+4,i+9] for i in range(8)],'Visit every element in reverse order exactly once.'),
])
add('missing_mapping_key', [
 ('user_alias','def solve(x):\n    alias = @\n    return alias.upper()','x.get("alias", "guest")','x["alias"]',[{'id':i} for i in range(8)],'Use guest for absent alias; uppercase the alias.'),
 ('stock_count','def solve(x):\n    stock = @\n    return stock + 5','x.get("stock", 0)','x["stock"]',[{'sku':i} for i in range(8)],'Absent stock starts at zero, then add five units.'),
 ('priority','def solve(x):\n    level = @\n    return "urgent" if level > 3 else "normal"','x.get("priority", 0)','x["priority"]',[{'ticket':i} for i in range(8)],'Missing priority means zero; levels above three are urgent.'),
 ('tax_rate','def solve(x):\n    rate = @\n    return 100 * (1 + rate)','x.get("tax", 0)','x["tax"]',[{'order':i} for i in range(8)],'Missing tax means zero; apply the rate to a base of 100.'),
 ('record_label','def solve(x):\n    text = @\n    return text.strip()','x.get("label", "")','x["label"]',[{'index':i} for i in range(8)],'Strip label whitespace; absent label is empty text.'),
 ('bonus_points','def solve(x):\n    bonus = @\n    return 10 + bonus','x.get("bonus", 0)','x["bonus"]',[{'player':i} for i in range(8)],'Add optional bonus points to ten; missing bonus is zero.'),
 ('language','def solve(x):\n    language = @\n    return language.lower()','x.get("language", "en")','x["language"]',[{'session':i} for i in range(8)],'Normalize language to lowercase, defaulting to en.'),
 ('discount','def solve(x):\n    discount = @\n    return 50 - discount','x.get("discount", 0)','x["discount"]',[{'invoice':i} for i in range(8)],'Subtract optional discount from fifty, defaulting to zero.'),
])
add('zero_denominator', [
 ('mean_score','def solve(x):\n    if @:\n        return 0.0\n    return sum(x) / len(x)','not x','False',[[]]*8,'Mean of values, or zero for an empty list.'),
 ('ratio','def solve(x):\n    numerator, denominator = x\n    if @:\n        return 0.0\n    return numerator / denominator','denominator == 0','False',[[i,0] for i in range(8)],'Return numerator/denominator; define zero denominator as zero.'),
 ('percentage','def solve(x):\n    part, total = x\n    if @:\n        return 0.0\n    return 100 * part / total','total == 0','False',[[i,0] for i in range(8)],'Percentage of total, with zero returned for zero total.'),
 ('batch_size','def solve(x):\n    items, workers = x\n    if @:\n        return 0\n    return items // workers','workers == 0','False',[[i+1,0] for i in range(8)],'Integer items per worker; zero workers means zero.'),
 ('normalise','def solve(x):\n    total = sum(x)\n    if @:\n        return [0.0 for value in x]\n    return [value / total for value in x]','total == 0','False',[[i,-i] for i in range(1,9)],'Normalize by sum, returning all zeroes when the sum is zero.'),
 ('cycle_slot','def solve(x):\n    position, size = x\n    if @:\n        return 0\n    return position % size','size == 0','False',[[i,0] for i in range(8)],'Return circular slot; an empty cycle has slot zero.'),
 ('unit_cost','def solve(x):\n    amount, units = x\n    if @:\n        return 0.0\n    return round(amount / units, 2)','units == 0','False',[[i*10,0] for i in range(8)],'Rounded unit cost; zero units means zero cost.'),
 ('speed','def solve(x):\n    distance, duration = x\n    if @:\n        return 0.0\n    return distance / duration','duration == 0','False',[[i+1,0] for i in range(8)],'Distance per duration; zero duration returns zero.'),
])
add('wrong_argument_count', [
 ('scaled_price','def scale(value, factor):\n    return value * factor\ndef solve(x):\n    return @','scale(x, 2)','scale(x)',list(range(8)),'Double the input using the scale helper.'),
 ('offset_reading','def offset(value):\n    return value + 3\ndef solve(x):\n    return @','offset(x)','offset(x, 3)',list(range(8)),'Offset each reading by three.'),
 ('round_price','def solve(x):\n    adjusted = x * 1.2\n    return @','round(adjusted, 2)','round()',[i+.123 for i in range(8)],'Multiply by 1.2 and round to two decimals.'),
 ('clamp_value','def clamp(value, lower, upper):\n    return min(max(value, lower), upper)\ndef solve(x):\n    return @','clamp(x, 0, 10)','clamp(x, 0)',list(range(8)),'Clamp a number into the range zero through ten.'),
 ('absolute_delta','def solve(x):\n    delta = x - 5\n    return @','abs(delta)','abs(delta, 0)',list(range(8)),'Return absolute distance from five.'),
 ('power_value','def solve(x):\n    return @','pow(x, 2)','pow(x)',list(range(8)),'Square the input.'),
 ('partition_count','def solve(x):\n    return @','divmod(x, 3)','divmod(x)',list(range(8)),'Return quotient and remainder on division by three.'),
 ('decorate','def join_label(prefix, value):\n    return prefix + str(value)\ndef solve(x):\n    return @','join_label("ID-", x)','join_label(x)',list(range(8)),'Prefix the input with ID-.'),
])

# Per-class ordering is fixed before training, never selected using test performance.
SPLITS = ('train','train','train','train','calibration','validation','test','test')
def catalog_rows():
    counts = {}
    for program in PROGRAMS:
        index = counts.get(program.label, 0); counts[program.label] = index+1
        yield program, SPLITS[index]
