import random

first_part = [
    "Tetra", "First", "Second", "Third", "Fourth"
]

any_part = [
    "Sword", "Bow", "Dungeon", "Fire", "Doom", "Chain", "Knot", "Key"
]

middle_part = [
    "of"
]

end_part = [
    "Friends", "Force"
]

# Uses lists above to generate a random
# name seperated by dashes
def generate_name():
    possible_first = first_part + any_part
    first = possible_first[random.randint(0,len(possible_first)-1)]
    possible_middle = middle_part + any_part
    middle = possible_middle[random.randint(0,len(possible_middle)-1)]
    possible_end = end_part + any_part
    end = possible_end[random.randint(0,len(possible_end)-1)]
    return first + "-" + middle + "-" + end

def is_name_free(name, table):
    resp = table.get_item(
        Key={
            "name" : name
        }
    )
    if 'Item' in resp:
        if 'name' in resp['Item']:
            return False
    return True

# Generate a random string (ASCII Only)
def random_string(length):
    val = ""
    for _ in range(length):
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
        val = val + (chr(random_integer))
    return val

def generate_unique_name(dynamodb_table):
    name = generate_name()
    tries = 0

    while not is_name_free(name, dynamodb_table):
        if tries < 5:
            name = generate_name()
        else:
            # Append a random string to end of random name if could
            # not generate a name within five tries.
            name = generate_name() + "-" + random_string(tries)
        tries = tries + 1
    

    return name

# Generates name when ran directly
if __name__ == '__main__':
    print(generate_name())