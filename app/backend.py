from flask import Flask
from flask import request
from datetime import datetime
import csv
import unidecode

def normalize(string):
  if string:
    return unidecode.unidecode(string).strip()
  return string

def extract_number(string):
  #print(string)
  if string == None or string == "":
    return None
  string = strip_leading_zeros(string)
  string = string.replace("X", "")
  return string

def estimate_birth_year(age, record_year):
  if age and len(age) > 0 and not age == "" and not record_year == "":
    age = float(age)
    if age < 1:
      age = 0
    return int(record_year-age)
  return ""

def create_equiv_dict():
  # THIS IS A VERY WRONG ASSOCTIATIONS OF THESE ABBRIVIATIONS!!!!
  assoc_list = ( (('SD','SGD', 'SLR', 'SJC'), 'San Diego'), (('SG','SGL', 'LA', 'MLA', 'NSG'), 'Los Angeles'),\
                (('SFR', 'SBV', 'SV', 'SB', 'BP', 'SI', 'SY', 'Si', 'LPC'), 'Santa Barbara'), \
                (('SLO', 'ST', 'SMA', 'Sma', 'SAP', 'SLD', 'SC', 'SJB'), 'Monterey'), \
                (('SCZ', 'SCL', 'SJS', 'SFB'), 'San Jose'), (('SFD', 'SRA', 'SFS'), 'San Francisco'),)
  equiv_dict = dict()
  for keys, value in assoc_list:
    for key in keys:
      equiv_dict[key] = value
  return equiv_dict

locations_dict = create_equiv_dict()

def estimate_location_w_mission(mission_abv):
  if not mission_abv == "":
    return locations_dict[mission_abv]
  else:
    return ""

def estimate_location_w_location(location):
  equiv_locs = {
      'Mission San Miguel, Baja California': 'Monterey',
      'Mission San Diego': 'San Diego',
      'Mission San Antonio': 'Monterey',
      'Mission San Carlos' : 'Monterey',
      'Mission San Buenaventura': 'Santa Barbara',
      'Mission San Juan Capistrano': 'San Diego',
      'Mission Santa Barbara': 'Santa Barbara',
      'Mission San Gabriel' : 'Los Angeles'
  }
  if location in equiv_locs.keys():
    return equiv_locs[location]
  else:
    return location

def export_attribute(attribute):
  string = ""
  if isinstance(attribute, list):
    for item in attribute:
      string += f"{item}, "
  else:
    string = attribute
  return string

class Person:
  def __init__(self, line_id, gender=None, race=[], origin=None, age=None,\
               record_year=None, baptismal_number=None, baptismal_mission=None,\
               death_mission=None, death_number=None,\
               location=None,\
               first_name=None, last_name=None, \

               spouse_first=None, spouse_last=None, \
               spouse_baptismal_mission = None, spouse_baptismal_number=None,\

               previous_spouse_first=None, previous_spouse_last=None,\
               previous_spouse_baptismal_mission=None, previous_spouse_baptismal_number=None,\
               previous_spouse_death_mission=None, previous_spouse_death_number =None,\

               father_first=None, father_last=None, \
               father_baptismal_mission = None, father_baptismal_number=None, \

               mother_first=None, mother_last=None, \
               mother_baptismal_mission = None, mother_baptismal_number=None,\

               children=[], \

               record_mission=None, \
               record_type=None, ):
    
    self.line_id = line_id
    self.tree_id = 0
    # highest_match = (confidence, associated_person)
    self.highest_match = None
    self.visited = False
    self.generation = 0
    self.head_of_family = False

    self.connected = False

    self.record_type = record_type

    if gender:
      gender = gender.lower()
    self.gender = gender
    self.race = race
    self.origin = origin
    self.location = location
    self.record_mission = record_mission
    self.baptismal_mission = baptismal_mission
    self.baptismal_number = extract_number(baptismal_number)
    self.death_mission = death_mission
    self.death_number = death_number
    self.birth_year_estimate = estimate_birth_year(age, record_year)
    self.record_year = record_year
    self.first_name = normalize(first_name)
    self.last_name = normalize(last_name)
    
    self.spouse_first = normalize(spouse_first)
    self.spouse_last = normalize(spouse_last)
    self.spouse_baptismal_mission = spouse_baptismal_mission
    self.spouse_baptismal_number = extract_number(spouse_baptismal_number)
    self.spouse_obj = None
    self.assembled_spouse_obj = None

    self.previous_spouse_first = normalize(previous_spouse_first)
    self.previous_spouse_last = normalize(previous_spouse_last)
    self.previous_spouse_baptismal_mission = previous_spouse_baptismal_mission
    self.previous_spouse_baptismal_number = extract_number(previous_spouse_baptismal_number)
    self.previous_spouse_death_mission = previous_spouse_death_mission
    self.previous_spouse_death_number = previous_spouse_death_number
    self.previous_spouse_obj = None
    self.assembled_previous_spouse_obj = None

    self.father_first = normalize(father_first)
    self.father_last = normalize(father_last)
    self.father_baptismal_mission = father_baptismal_mission
    self.father_baptismal_number = extract_number(father_baptismal_number)
    self.father_obj = None
    self.assembled_father_obj = None

    self.mother_first = normalize(mother_first)
    self.mother_last = normalize(mother_last)
    self.mother_baptismal_mission = mother_baptismal_mission
    self.mother_baptismal_number = extract_number(mother_baptismal_number)
    self.mother_obj = None
    self.assembled_mother_obj = None

    self.children = [normalize(child) for child in children]
    self.children_objs = []
    self.assembled_children_objs = []

  def export_person_string(self):
    main_string = "{\n"

    person = f"name: '{export_attribute(self.first_name)} {export_attribute(self.last_name)}',\n" \
              "attributes: {\n"\
              f"gender: '{export_attribute(self.gender)}',\n"\
              f"race: '{export_attribute(self.race)}',\n"\
              f"origin: '{export_attribute(self.origin)}',\n"\
              f"location: '{export_attribute(self.location)}',\n"\
              "},\n"
    main_string = main_string + person + self.export_children_string() + "},"
    return main_string
  
  def export_children_string(self):
    children_strings = []
    for child in self.assembled_children_objs:
      children_strings.append(child.export_person_string())
    
    main_string = "children: [\n"
    for child_str in children_strings:
      main_string+=child_str
    main_string+="]\n"

    return main_string

  def export_person(self):
    return {
        "first_name": self.first_name,
        "last_name": self.last_name,
        "race": self.race,
        "gender": self.gender,
        "origin":self.origin,
        "location":self.location,
        "baptismal_mission": self.baptismal_mission,
        "baptismal_number": self.baptismal_number,
        "record_missions": self.record_mission
    }
  

  def exists(self):
    if (self.origin != "" and self != None) or \
        (self.first_name != "" and self.first_name != None) or \
        (self.last_name != "" and self.last_name != None) or \
        (self.baptismal_mission != "" and self.baptismal_mission != None) or \
        (self.baptismal_number != "" and self.baptismal_number != None) or \
        (self.death_mission != "" and self.death_mission != None) or \
        (self.death_number != "" and self.death_number != None):
        return True
    return False
  
  def set_childrens_race(self):
    for child in self.assembled_children_objs:
      #If parents have multiple races
      if isinstance(self.race, list):
        for race in self.race: #Iterate over every race the parent is assigned

          if isinstance(child.race, list): #If child has multiple races 
            if race not in child.race: #If parents race not in childs multiple races
              child.race.append(race) #add the parents race to the childs
          
          else: #If child only has one race
            if race != child.race: #If the parents race != childs race
              child.race = [child.race]
              child.race.append(race)

      else: #If parent only has one race
        if isinstance(child.race, list): #If child has multiple
            child.race.append(self.race)
          
        else: #If child has one
          child.race = [child.race]
          child.race.append(self.race)
  
  def set_childens_gen(self):
    for child in self.assembled_children_objs:
      child.generation = self.generation + 1
      # print(f"Setting {child.first_name} generation to {child.generation}")

  def set_parent_gen(self):
    if self.assembled_mother_obj != None:
      self.assembled_mother_obj.generation = self.generation + 1
    if self.assembled_father_obj != None:
      self.assembled_father_obj.generation = self.generation + 1

  def print_all(self):
    print(f"Record Type: {self.record_type} \n"+
            f"Gender: {self.gender} \n" +
            f"Race: {self.race}\n" +
            f"Origin: {self.origin}\n" + 
            f"Location: {self.location}\n" +
            f"Record Mission: {self.record_mission}\n" +
            f"Baptismal Mission: {self.baptismal_mission}\n"+
            f"Baptismal Number: {self.baptismal_number}\n"+
            f"Death Mission: {self.death_mission}\n"+
            f"Death Number: {self.death_number}\n"+
            f"Birth Year Estimate: {self.birth_year_estimate} \n"+
            f"Record year: {self.record_year}\n"+
            f"\n"+
            f"First Name: {self.first_name}\n"+
            f"Last Name: {self.last_name}\n"+
            "\n"+
            f"Spouse Assembled: {self.assembled_spouse_obj != None}\n"+
            f"Spouse First: {self.spouse_first}\n"+
            f"Spouse Last: {self.spouse_last}\n"+
            f"Spouse Baptismal Mission: {self.spouse_baptismal_mission}\n"+
            f"Spouse Baptismal Number: {self.spouse_baptismal_number}\n"+
            "\n"+
            f"Previous Spouse Assembled: {self.assembled_previous_spouse_obj != None}\n"+
            f"Previous Spouse First: {self.previous_spouse_first}\n"+
            f"Previous Spouse Last: {self.previous_spouse_last}\n"+
            f"Previous Spouse Baptismal Mission: {self.previous_spouse_baptismal_mission}\n"+
            f"Previous Spouse Baptismal Number: {self.previous_spouse_baptismal_number}\n"+
            f"Previous Spouse Death Mission: {self.previous_spouse_death_mission}\n"+
            f"Previous Spouse Death Number: {self.previous_spouse_death_number}\n"+
            "\n"+
            f"Father Assembled: {self.assembled_father_obj != None}\n"+
            f"Father First: {self.father_first}\n"+
            f"Father Last: {self.father_last}\n"+
            f"Father Baptismal Mission: {self.father_baptismal_mission}\n"+
            f"Father Baptimsal Number: {self.father_baptismal_number}\n"+
            "\n"+
            f"Mother Assembled: {self.assembled_mother_obj != None}\n"+
            f"Mother First: {self.mother_first}\n"+
            f"Mother Last: {self.mother_last}\n"+
            f"Mother Baptismal Mission: {self.mother_baptismal_mission}\n"+
            f"Mother Baptimsal Number: {self.mother_baptismal_number}\n"+
            "\n"+
            f"LenAssembledChildObjs: {len(self.assembled_children_objs)}, LenChildObjs: {len(self.children_objs)}\n"
            f"Children: {self.children}")


  def __repr__(self):
    return f"(Line_Id: {self.line_id}, Record Type: {self.record_type}, BapMission: {self.baptismal_mission}, BapNumber: {self.baptismal_number}, Location:{self.location}, Gender: {self.gender}, First: {self.first_name}, Last: {self.last_name}, Spouse First: {self.spouse_first}, Spouse Last: {self.spouse_last}, Mother First: {self.mother_first}, Mother Last: {self.mother_last}, Father First: {self.father_first}, Father Last: {self.father_last}, Children: {self.children})"

def add_person_to_family(person, families): #Based off of FIRST NAMES!!!
  if not person.first_name in families:
    families[person.first_name] = []
    families[person.first_name].append(person)
  else:
    families[person.first_name].append(person)

def add_origin(origin, origins):
  if (not origin in origins) and (not origin == ""):
    origins.append(origin)
  return origins

def add_race(race, races):
  if not race in races and (not race == ""):
    races.append(race)
  return races

def add_missions(mission, missions): 
  if not mission in missions and (not mission == ""):
    missions.append(mission)
  return missions

def add_location(location, locations):
  if not location in locations and (not location == ""):
    locations.append(location)
  return locations


census_families = {}
census_people_arr = []

census_origins = []
census_races = []
census_locations = []

people = 0

def split_census_races(race):
  race = race.replace(" ", "")
  if "," in race:
    new_races = []
    races = race.split(",")

    for race in races:
      if race != "":
        new_races.append(normalize(race))

    if len(new_races) == 1:
      return normalize(new_races[0])

    return new_races
  return normalize(race)

with open("censusData.tsv") as fd:
  rd = csv.reader(fd, delimiter="\t", quotechar='"')
  next(rd)
  # Revisit this line_id_ctr!!!!!!
  line_id = 2
  for row in rd:
    gender = row[7]
    race = row[6]

    race = split_census_races(race)

    census_races = add_race(race, census_races)
    location = row[0]
    #census_locations = add_location(location, census_locations)
    origin = row[8]
    census_origins = add_origin(origin, census_origins)
    first_name = row[1]
    last_name = row[3]
    age = row[9]
    spouse_first = row[10]
    spouse_last = row[11]
    father_first = row[12]
    father_last = row[13]
    mother_first = row[14]
    mother_last = row[15]
    children = [child for child in row[16:30] if child != ""]

    # person = Person(line_id, gender=None, race=None, origin=None, age=None,\
          # record_year=None, baptismal_number=None, baptismal_mission=None,\
          # location=None,\
          # first_name=None, last_name=None, \

          # spouse_first=None, spouse_last=None, \
          # spouse_baptismal_mission = None, spouse_baptismal_number=None,\

          # father_first=None, father_last=None, \
          # father_baptismal_mission = None, father_baptismal_number=None, \

          # mother_first=None, mother_last=None, \
          # mother_baptismal_mission = None, mother_baptismal_number=None,\

          # children=None, children_objs=[], \

          # record_mission=None, \
          # record_type=None, )


    #THE PERSON CONSTRUCTOR HAS BEEN CHANGED SINCE THIS WAS LAST UPDATED!!!!
    person = Person(line_id, gender=gender, race=race, origin=origin, age=age,\
          record_year=1790, baptismal_number=None, baptismal_mission=None,\
          location=location,\
          first_name=first_name, last_name=last_name, \

          spouse_first=spouse_first, spouse_last=spouse_last, \
          spouse_baptismal_mission = None, spouse_baptismal_number=None,\

          father_first=father_first, father_last=father_last, \
          father_baptismal_mission = None, father_baptismal_number=None, \

          mother_first=mother_first, mother_last=mother_last, \
          mother_baptismal_mission = None, mother_baptismal_number=None,\

          #Children are listed in the spreadsheet under seperate entries, children_objs will be assembled during family tree assembly.
          children=children,\

          record_mission=None, \
          record_type="Census", )
    
    # person.location = estimate_location_w_location(location) REVISIT THIS LATER!!!

    census_people_arr.append(person)
    add_person_to_family(person, census_families)
    people += 1
    line_id += 1


# universal_families["BaptismalMission"]["BaptismalNumber"] = Person[] <-- array of person objects assembeled from different documents
universal_families = {}

people_in_universal_families = 0

#Universal Family Lookup
#Look Up by mission and number in the Mission
def universal_family_lookup(mission, number):
  person_arr = universal_families[mission][number]
  #for person in person_arr:
    #print(f"Record Type: {person.record_type} Record Line: {person.line_id} {person}")
  return person_arr

# def universal_family_search()

def strip_leading_zeros(string):
  stripped=False
  while not stripped:
    if string[0] == "0":
      string = string[1:]
    else:
      stripped=True
  return string

def add_to_universal_families(person, people_in_universal_families):
  if person.baptismal_mission != "" and person.baptismal_mission != None and\
  person.baptismal_number != "" and person.baptismal_number != None:

    person.baptismal_number = extract_number(person.baptismal_number)

    if person.baptismal_mission in universal_families:
    
      if person.baptismal_number in universal_families[person.baptismal_mission]:
        universal_families[person.baptismal_mission][person.baptismal_number].append(person)
      else:
        universal_families[person.baptismal_mission][person.baptismal_number] = [person]
        people_in_universal_families += 1
    
    else:
      universal_families[person.baptismal_mission] = {}
      universal_families[person.baptismal_mission][person.baptismal_number] = [person]
      people_in_universal_families += 1

  return people_in_universal_families
    
baptism_families = {}
baptism_missions = []

earliest_record = datetime.max.date()
latest_record = datetime.min.date()

age_cnt = 0

indexErrors = 0

with open("baptismData.tsv") as fd:
  rd = csv.reader(fd, delimiter="\t", quotechar='"')
  next(rd)
  
  for row in rd:
    try:

      line_id_ctr = row[0]

      record_year = ""
      if (not row[40] == "") and (not row[40] == "-"):
        record_date = datetime.strptime(row[40], "%m/%d/%Y").date()
        record_year = record_date.year
        if record_date > latest_record:
         latest_record = record_date
        if record_date < earliest_record:
          earliest_record = record_date

      gender = row[43]
      race = row[29]
      origin = row[30]

      age = row[34]
      if not age == "" and len(age) > 0:
        try:
          float(age)
        except:
          age_cnt+=1;
          age = ""

      # age = handle_age(row[34])
      
      record_mission = row[4]
      baptismal_mission = row[4]
      baptismal_number = row[38]
      baptism_missions = add_missions(baptismal_mission, baptism_missions)
      surname = row[31]
      spanish_name = row[33]

      mother_baptismal_mission = row[2]
      mother_baptismal_number = row[11]
      mother_race = row[13]
      mother_origin = row[14]
      mother_surname = row[15]
      mother_spanish_name = row[17]

      father_baptismal_mission = row[3]
      father_baptismal_number = row[25]
      father_military_status = row[18]
      father_religious_status = row[19]
      father_race = row[20]
      father_origin = row[21]
      father_surname = row[22]
      father_spanish_name = row[24]    

      # person = Person(line_id, gender=None, race=None, origin=None, age=None,\
               # record_year=None, baptismal_number=None, baptismal_mission=None,\
               # location=None,\
               # first_name=None, last_name=None, \

               # spouse_first=None, spouse_last=None, \
               # spouse_baptismal_mission = None, spouse_baptismal_number=None,\

               # father_first=None, father_last=None, \
               # father_baptismal_mission = None, father_baptismal_number=None, \

               # mother_first=None, mother_last=None, \
               # mother_baptismal_mission = None, mother_baptismal_number=None,\

               # children=None, children_objs=[], \

               # record_mission=None, \
               # record_type=None, )

      person_baptised = Person(line_id_ctr, gender, race, origin, age,\
                      record_year, baptismal_number, baptismal_mission,\
                      first_name=spanish_name, last_name=surname, \

                      father_first=father_spanish_name, father_last=father_surname,\
                      father_baptismal_mission=father_baptismal_mission, father_baptismal_number=father_baptismal_number,\

                      mother_first=mother_spanish_name, mother_last=mother_surname,\
                      mother_baptismal_mission = mother_baptismal_mission, mother_baptismal_number = mother_baptismal_number,\

                      record_mission = record_mission,\
                      record_type="Baptism"
                      )
      
      mother_of_baptised = Person(line_id_ctr, "f", mother_race, mother_origin,\
                               first_name=mother_spanish_name, last_name=mother_surname,\
                               record_year=record_year, baptismal_number=mother_baptismal_number,\
                               baptismal_mission=mother_baptismal_mission,\

                               spouse_first=father_spanish_name, spouse_last=father_surname,\
                               spouse_baptismal_mission=father_baptismal_mission, spouse_baptismal_number=father_baptismal_number,\
                               children=[person_baptised.first_name],
                               record_mission=record_mission,
                               record_type="Mother of Baptised"
                               )
      
      father_of_baptised = Person(line_id_ctr, "m", father_race, father_origin,\
                               first_name=father_spanish_name, last_name=father_surname,\
                               record_year=record_year, baptismal_number=father_baptismal_number,\
                               baptismal_mission=father_baptismal_mission,\
                               spouse_first=mother_spanish_name, spouse_last=mother_surname,\
                               spouse_baptismal_mission=mother_baptismal_mission, spouse_baptismal_number=mother_baptismal_number,\

                               children=[person_baptised.first_name],
                               record_mission=record_mission,
                               record_type="Father of Baptised"
                               )
      
      if mother_of_baptised.exists():
        person_baptised.mother_obj = mother_of_baptised
        mother_of_baptised.children_objs.append(person_baptised)
        people_in_universal_families = add_to_universal_families(mother_of_baptised, people_in_universal_families)
      
      if father_of_baptised.exists():
        person_baptised.father_obj = father_of_baptised
        father_of_baptised.children_objs.append(person_baptised)
        people_in_universal_families = add_to_universal_families(father_of_baptised, people_in_universal_families)

      if mother_of_baptised.exists() and father_of_baptised.exists():
        mother_of_baptised.spouse_obj = father_of_baptised
        father_of_baptised.spouse_obj = mother_of_baptised

      people_in_universal_families = add_to_universal_families(person_baptised, people_in_universal_families)
      
      #add_person_to_family(person_baptised, baptism_families)

    except IndexError:
      indexErrors += 1

#print(f"Races Len: {len(census_races)}")

print(f"Age Cnt: {age_cnt}")
print(f"Index Errors: {indexErrors}")


import re

death_families = {}
death_missions = []

earliest_record = datetime.max.date()
latest_record = datetime.min.date()

indexErrors = 0

with open("deathData.tsv") as fd:
  rd = csv.reader(fd, delimiter="\t", quotechar='"')
  next(rd)
  for row in rd:
    try:

      line_id_ctr = row[0]

      record_year = ""
      if (not row[37] == "") and (not row[37] == "-"):
        record_date = datetime.strptime(row[37], "%m/%d/%Y").date()
        record_year = record_date.year
        if record_date > latest_record:
         latest_record = record_date
        if record_date < earliest_record:
          earliest_record = record_date

      race = row[25]
      origin = row[26]

      age = row[30]
      if not age == "" and len(age) > 0:
        try:
          float(age)
        except:
          age_cnt+=1;
          age = ""

      # age = handle_age(row[34])
      
      record_mission = row[19]
      baptismal_mission = row[22]
      baptismal_number = row[1]
      surname = row[27]
      spanish_name = row[29]

      mother_religious_status = row[3]
      mother_race = row[4]
      mother_origin = row[5]
      mother_spanish_name = row[6]
      # Death records only have a "Name field, this splits them into first and last names"
      if "(" in mother_spanish_name:
        search = re.search("\((.*)\)", mother_spanish_name).group(1)
        mother_spanish_name = mother_spanish_name.replace(f"({search})", "")
      
      if "[" in mother_spanish_name:
        search = re.search("\[(.*)\]", mother_spanish_name).group(1)
        #Sometimes the [] are used to say what should have been there, other times it tells if the person in question is dead or not, sometimes it gives an alternative name.
        if len(search) <= 3:
          mother_spanish_name = mother_spanish_name.replace("[", "")
          mother_spanish_name = mother_spanish_name.replace("]", "")
        else:
          mother_spanish_name = mother_spanish_name.replace(f"[{search}]", "")

      if "," in mother_spanish_name:
        mother_first, mother_last = mother_spanish_name.split(",", 1)
        
      father_religious_status = row[7]
      father_race = row[8]
      father_origin = row[9]
      father_spanish_name = row[10]   
      # Death records only have a "Name field, this splits them into first and last names"
      if "(" in father_spanish_name:
        search = re.search("\((.*)\)", father_spanish_name).group(1)
        father_spanish_name = father_spanish_name.replace(f"({search})", "")
      
      if "[" in father_spanish_name:
        search = re.search("\[(.*)\]", father_spanish_name).group(1)
        #Sometimes the [] are used to say what should have been there, other times it tells if the person in question is dead or not, sometimes it gives an alternative name.
        if len(search) <= 3:
          father_spanish_name = father_spanish_name.replace("[", "")
          father_spanish_name = father_spanish_name.replace("]", "")
        else:
          father_spanish_name = father_spanish_name.replace(f"[{search}]", "")

      if "," in father_spanish_name:
        father_first, father_last = father_spanish_name.split(",", 1)

      spouse_religious_status = row[11]
      spouse_race = row[12]
      spouse_origin = row[13]
      spouse_spanish_name = row[14] 
      # Death records only have a "Name field, this splits them into first and last names"


      # A problem occurs with BP 26, double check them in universal person when finished
      # There is a case where someones alternative name is entered in as well as their "normal" name, I'm going to handle that later
      """
      if "[" in spouse_spanish_name:
          spouse_alt_name = re.search("\[(.*)\]", spouse_spanish_name).group(1)
          if "," in spouse_alt_name:
            spouse_alt_first, spouse_alt_last = spouse_alt_name.split(",")
          else:
            spouse_alt_first = spouse_alt_name
          spouse_spanish_name.replace(f"[{spouse_alt_name}]", "")"""

      #print(line_id_ctr)
      #print(spouse_spanish_name)

      #Fixes individule case
      if line_id_ctr == "58101":
        spouse_spanish_name = "Angel Clavasio Temeiasuit"

      if "(" in spouse_spanish_name:
        #Fixes individule case
        if "(difunto" in spouse_spanish_name:
          spouse_spanish_name = spouse_spanish_name.replace("(difunto", "(difunto)")
        search = re.search("\((.*)\)", spouse_spanish_name).group(1)
        spouse_spanish_name = spouse_spanish_name.replace(f"({search})", "")
      
      if "[" in spouse_spanish_name:
        #print(spouse_spanish_name)
        #print(line_id_ctr)

        search = re.search("\[(.*)\]", spouse_spanish_name).group(1)

        #Sometimes the [] are used to say what should have been there, other times it tells if the person in question is dead or not, sometimes it gives an alternative name.
        if len(search) <= 3:
          spouse_spanish_name = spouse_spanish_name.replace("[", "")
          spouse_spanish_name = spouse_spanish_name.replace("]", "")
        else:
          spouse_spanish_name = spouse_spanish_name.replace(f"[{search}]", "")

      if "," in spouse_spanish_name:
        spouse_first, spouse_last = spouse_spanish_name.split(",", 1)

      person = Person(line_id_ctr, race=race, origin=origin, age=age,\
                      record_year=record_year, baptismal_number=baptismal_number, baptismal_mission=baptismal_mission,\
                      first_name=spanish_name, last_name=surname, \
                      spouse_first=spouse_first, spouse_last=spouse_last,\

                      father_first=father_first,\
                      mother_first=mother_first,\

                      record_mission = record_mission,\
                      record_type="Death"
                      )
      
      spouse = Person(line_id_ctr, race=spouse_race, origin=spouse_origin,\
                      record_year=record_year,\
                      first_name=spouse_first, last_name=spouse_last, \
                      spouse_first=spanish_name, spouse_last=surname, \
                      record_mission = record_mission,\
                      record_type="Spouse of Deceased"
                      )

      mother = Person(line_id_ctr, race=mother_race, origin=mother_origin,\
                      record_year=record_year, gender="f",\
                      first_name=mother_first, last_name=mother_last, \
                      spouse_first=father_first, spouse_last=father_last, \
                      children = [spanish_name], record_mission = record_mission,\
                      record_type="Mother of Deceased"
                      )
      

      father = Person(line_id_ctr, race=father_race, origin=father_origin,\
                      record_year=record_year, gender="m",\
                      first_name=father_first, last_name=father_last, \
                      spouse_first=mother_first, spouse_last=mother_last, \
                      children = [spanish_name], record_mission = record_mission,\
                      record_type="Father of Deceased"
                      )
      
      if spouse.exists():
        person.spouse_obj = spouse
        people_in_universal_families = add_to_universal_families(spouse, people_in_universal_families)
      
      if mother.exists():
        person.mother_obj = mother
        mother.children_objs.append(person)
        people_in_universal_families = add_to_universal_families(mother, people_in_universal_families)
      
      if father.exists():
        person.father_obj = father
        father.children_objs.append(person)
        people_in_universal_families = add_to_universal_families(father, people_in_universal_families)
      
      if father.exists() and mother.exists():
        mother.spouse_obj = father
        father.spouse_obj = mother
      
      people_in_universal_families = add_to_universal_families(person, people_in_universal_families)

    except IndexError:
      indexErrors += 1

#print(f"Races Len: {len(census_races)}")

print(f"Age Cnt: {age_cnt}")
print(f"Index Errors: {indexErrors}")

from datetime import datetime

def has_prev_spouse(person):
  if (person.origin != "" and person != None) or \
      (person.first_name != "" and person.first_name != None) or \
      (person.baptismal_mission != "" and person.baptismal_mission != None) or \
      (person.baptismal_number != "" and person.baptismal_number != None) or \
      (person.death_mission != "" and person.death_mission != None) or \
      (person.death_number != "" and person.death_number != None):
      return True
  return False

marriage_data_families = {}
marriage_data_people_arr = []

marriage_data_people = 0

marriage_races = []
marriage_origins = []

marriage_missions = []
all_missions = []
bride_missions = []
groom_missions = []

existingBNumbers = 0
missingBNumbers = 0

earliest_marriage = datetime.max.date()
latest_marriage = datetime.min.date()

with open("marriageData.tsv") as fd:
  rd = csv.reader(fd, delimiter="\t", quotechar='"')
  next(rd)
  for row in rd:

    line_id_ctr = row[0]

    if not row[1] == "":
      marriage_date = datetime.strptime(row[1], "%m/%d/%Y").date()
      marriage_year = marriage_date.year
      if marriage_date > latest_marriage:
        latest_marriage = marriage_date
      if marriage_date < earliest_marriage:
        earliest_marriage = marriage_date

    marriage_mission = row[29]
    
    bride_race = row[3]
    bride_origin = row[4]
    bride_age = row[5]
    bride_baptismal_mission = row[8]
    bride_baptismal_number = row[7]
    bride_surname = row[11]
    bride_spanish_name = row[13]

    previous_husband_name = row[56]
    previous_husband_origin = row[57]
    previous_husband_baptismal_mission = row[58]
    previous_husband_baptismal_number = row[60]
    #SOME PH's DONT HAVE BAPTISMAL NUMBERS, BUT DO DEATH!!! THIS IS NOT HANDLED YET!!!
    previous_husband_death_mission = row[59]
    previous_husband_death_number = row[61]

    groom_race = row[17]
    groom_origin = row[18]
    groom_age = row[19]
    groom_baptismal_mission = row[22]
    groom_baptismal_number = row[21]
    groom_surname = row[31]
    groom_spanish_name = row[33]

    previous_wife_name = row[34]
    previous_wife_origin = row[35]
    previous_wife_baptismal_mission = row[36]
    previous_wife_baptismal_number = row[14]
    #SOME PW's DONT HAVE BAPTISMAL NUMBERS, BUT DO DEATH!!! THIS IS NOT HANDLED YET!!!
    previous_wife_death_mission = row[37]
    previous_wife_death_number = row[38]

    # This is the GFName entry, I am going to assume for future use that first name is the same as spanish name
    groom_father_spanish_name = row[39]
    groom_father_surname = row[41]
    groom_father_origin = row[42]
    groom_father_race = row[43]
    groom_father_baptismal_mission = row[45]
    groom_father_baptismal_number = row[46]
   
    groom_mother_spanish_name = row[47]
    groom_mother_surname = row[49]
    groom_mother_origin = row[50]
    groom_mother_race = row[51]
    groom_mother_baptismal_mission = row[53]
    groom_mother_baptismal_number = row[54]

    bride_father_spanish_name = row[64]
    bride_father_surname = row[66]
    bride_father_origin = row[67]
    bride_father_race = row[68]
    bride_father_baptismal_mission = row[62]
    bride_father_baptismal_number = row[63]

    bride_mother_spanish_name = row[70]
    bride_mother_surname = row[71]
    bride_mother_origin = row[72]
    bride_mother_race = row[73]
    bride_mother_baptismal_mission = row[75]
    bride_mother_baptismal_number = row[76]

    # person = Person(line_id, gender=None, race=None, origin=None, age=None,\
               # record_year=None, baptismal_number=None, baptismal_mission=None,\
               # location=None,\
               # first_name=None, last_name=None, \

               # spouse_first=None, spouse_last=None, \
               # spouse_baptismal_mission = None, spouse_baptismal_number=None,\

               # previous_spouse_first=None, previous_spouse_last=None,\
               # previous_spouse_baptismal_mission=None, previous_spouse_baptismal_number=None,\

               # father_first=None, father_last=None, \
               # father_baptismal_mission = None, father_baptismal_number=None, \

               # mother_first=None, mother_last=None, \
               # mother_baptismal_mission = None, mother_baptismal_number=None,\

               # children=[], children_objs=[], \

               # record_mission=None, \
               # record_type=None, )

    bride = Person(line_id_ctr, "f", bride_race, bride_origin, bride_age,\
                record_year, bride_baptismal_number, bride_baptismal_mission,\
                first_name=bride_spanish_name, last_name=bride_surname, \

                spouse_first=groom_spanish_name, spouse_last=groom_surname,\
                spouse_baptismal_mission=groom_baptismal_mission, spouse_baptismal_number=groom_baptismal_number,\

                previous_spouse_first=previous_husband_name,\
                previous_spouse_baptismal_mission = previous_husband_baptismal_mission, previous_spouse_baptismal_number=previous_husband_baptismal_number,\
                previous_spouse_death_mission=previous_husband_death_mission, previous_spouse_death_number=previous_husband_death_number,\

                father_first=bride_father_spanish_name, father_last=bride_father_surname,\
                father_baptismal_mission=bride_father_baptismal_mission, father_baptismal_number=bride_father_baptismal_number,\

                mother_first=bride_mother_spanish_name, mother_last=bride_mother_surname,\
                mother_baptismal_mission = bride_mother_baptismal_mission, mother_baptismal_number = bride_mother_baptismal_number,\

                record_mission = record_mission,\
                record_type="Bride Marriage"
                )
    
    groom = Person(line_id_ctr, "m", groom_race, groom_origin, groom_age,\
              record_year, groom_baptismal_number, groom_baptismal_mission,\
              first_name=groom_spanish_name, last_name=groom_surname, \

              spouse_first=bride_spanish_name, spouse_last=bride_surname,\
              spouse_baptismal_mission=bride_baptismal_mission, spouse_baptismal_number=bride_baptismal_number,\

              previous_spouse_first=previous_wife_name,\
              previous_spouse_baptismal_mission = previous_wife_baptismal_mission, previous_spouse_baptismal_number=previous_wife_baptismal_number,\
              previous_spouse_death_mission=previous_wife_death_mission, previous_spouse_death_number=previous_wife_death_number,\

              father_first=groom_father_spanish_name, father_last=groom_father_surname,\
              father_baptismal_mission=groom_father_baptismal_mission, father_baptismal_number=groom_father_baptismal_number,\

              mother_first=groom_mother_spanish_name, mother_last=groom_mother_surname,\
              mother_baptismal_mission = groom_mother_baptismal_mission, mother_baptismal_number = groom_mother_baptismal_number,\

              record_mission = record_mission,\
              record_type="Groom Marriage"
            )
    
    previous_husband = Person(line_id_ctr, "m", origin=previous_husband_origin, \
                              first_name=previous_husband_name,\
                              baptismal_mission=previous_husband_baptismal_mission,\
                              baptismal_number=previous_husband_baptismal_number,\

                              death_mission=previous_husband_death_mission, death_number=previous_husband_death_number,\
                              record_mission = record_mission,\
                              record_type="Previous Husband"
                              )
    
    previous_wife = Person(line_id_ctr, "f", origin=previous_wife_origin, \
                          first_name=previous_wife_name,\
                          baptismal_mission=previous_wife_baptismal_mission,\
                          baptismal_number=previous_wife_baptismal_number,\

                          death_mission=previous_wife_death_mission, death_number=previous_wife_death_number,\
                          record_mission = record_mission,\
                          record_type="Previous Wife"
                          )
    
    bride_mother = Person(line_id_ctr, "f", bride_mother_race, bride_mother_origin,\
                record_year=record_year, baptismal_number=bride_mother_baptismal_number, baptismal_mission=bride_mother_baptismal_mission,\
                first_name=bride_mother_spanish_name, last_name=bride_mother_surname, \

                spouse_first=bride_father_spanish_name, spouse_last=bride_father_surname,\
                spouse_baptismal_mission=bride_father_baptismal_mission, spouse_baptismal_number=bride_father_baptismal_number,\

                record_mission = record_mission,\
                record_type="Bride Mother"
                )

    bride_father = Person(line_id_ctr, "m", bride_father_race, bride_father_origin,\
                record_year=record_year, baptismal_number=bride_father_baptismal_number, father_baptismal_mission=bride_father_baptismal_mission,\
                first_name=bride_father_spanish_name, last_name=bride_father_surname, \

                spouse_first=bride_mother_spanish_name, spouse_last=bride_mother_surname,\
                spouse_baptismal_mission=bride_mother_baptismal_mission, spouse_baptismal_number=bride_mother_baptismal_number,\

                record_mission = record_mission,\
                record_type="Bride Father"
                )
    
    groom_mother = Person(line_id_ctr, "f",groom_mother_race, groom_mother_origin,\
                record_year=record_year, baptismal_number=groom_mother_baptismal_number, baptismal_mission=groom_mother_baptismal_mission,\
                first_name=groom_mother_spanish_name, last_name=groom_mother_surname, \

                spouse_first=groom_father_spanish_name, spouse_last=groom_father_surname,\
                spouse_baptismal_mission=groom_father_baptismal_mission, spouse_baptismal_number=groom_father_baptismal_number,\

                record_mission = record_mission,\
                record_type="Groom Mother"
                )

    groom_father = Person(line_id_ctr, "m", groom_father_race, groom_father_origin,\
                record_year=record_year, baptismal_number=groom_father_baptismal_number, baptismal_mission=groom_father_baptismal_mission,\
                first_name=groom_father_spanish_name, last_name=groom_father_surname, \

                spouse_first=groom_mother_spanish_name, spouse_last=groom_mother_surname,\
                spouse_baptismal_mission=groom_mother_baptismal_mission, spouse_baptismal_number=groom_mother_baptismal_number,\

                record_mission = record_mission,\
                record_type="Groom Father"
                )

    groom.spouse_obj = bride
    bride.spouse_obj = groom

    if previous_wife.exists():
      groom.previous_spouse_obj = previous_wife
      previous_wife.previous_spouse_obj = groom   

    if previous_husband.exists():
      bride.previous_spouse_obj = previous_husband
      previous_husband.previous_spouse_obj = bride

    if bride_mother.exists():
      bride.mother_obj = bride
      bride_mother.children.append(bride.first_name)
      bride_mother.children_objs.append(bride)
    if bride_father.exists():
      bride.father_obj = bride
      bride_father.children.append(bride.first_name)
      bride_father.children_objs.append(bride)

    if groom_mother.exists():
      groom.mother_obj = groom_mother
      groom_mother.children.append(groom.first_name)
      groom_mother.children_objs.append(groom)
    if groom_father.exists():
      groom.father_obj = groom_father
      groom_father.children.append(groom.first_name)
      groom_father.children_objs.append(groom)
    
    if groom_mother.exists() and groom_father.exists():
      groom_mother.spouse_obj = groom_father
      groom_father.spouse_obj = groom_mother

    if bride_mother.exists() and bride_father.exists():
      bride_mother.spouse_obj = bride_father
      bride_father.spouse_obj = bride_mother

    people_in_universal_families=add_to_universal_families(groom,people_in_universal_families)
    people_in_universal_families=add_to_universal_families(bride,people_in_universal_families)

    if groom_mother.exists():
      people_in_universal_families=add_to_universal_families(groom_mother,people_in_universal_families)
    if groom_father.exists():
      people_in_universal_families=add_to_universal_families(groom_father,people_in_universal_families)
    if bride_mother.exists():
      people_in_universal_families=add_to_universal_families(bride_mother,people_in_universal_families)
    if bride_father.exists():
      people_in_universal_families=add_to_universal_families(bride_father,people_in_universal_families)
    if previous_husband.exists():
      people_in_universal_families=add_to_universal_families(previous_husband,people_in_universal_families)
    if previous_wife.exists():
      people_in_universal_families=add_to_universal_families(previous_wife,people_in_universal_families)
    
    #marriage_data_people_arr.append(bride)
    #marriage_data_people_arr.append(groom)
   
    marriage_data_people += 1


def person_lookup(mission, number):
  person = created_by_bap[mission][number]
  return person

def add_to_unregistered_people(person):
  #They may not have a first name...
  if person.first_name == None:
    person.first_name = ""

  #Initialize unregistered_people dict
  if unregistered_people[person.first_name] == None:
    unregistered_people[person.first_name] = []
  unregistered_people[person.first_name].append(person)

def add_to_created_by_bap(person):

  #If a person's baptismal mission or number is blank, then they exist but are not registered with a mission
  #Add them to the unregistered_people dict
  if person.baptismal_mission == None or person.baptismal_number == None\
   or person.baptismal_mission == "" or person.baptismal_number == "":
    return
  else:
    person.baptismal_number = extract_number(person.baptismal_number)

  if person.baptismal_mission in created_by_bap:
    created_by_bap[person.baptismal_mission][person.baptismal_number] = person
  
  else:
    created_by_bap[person.baptismal_mission] = {}
    created_by_bap[person.baptismal_mission][person.baptismal_number] = person

def contains_child(arr, new_child):
  for child in arr:
    if child.baptismal_mission == new_child.baptismal_mission and child.baptismal_number == new_child.baptismal_number:
      return True
  return False

def in_bap_dict(person, baptismal_dict):
  if person.baptismal_mission in baptismal_dict.keys():
    if baptismal_dict[person.baptismal_mission] != None and person.baptismal_number in baptismal_dict[person.baptismal_mission].keys():
      return baptismal_dict[person.baptismal_mission][person.baptismal_number]
  return None

from typing import List
def set_field(new_person_value, record_value):

  if record_value == "":
    record_value = None

  if new_person_value == "":
    new_person_value = None

  # If record value is None
  if (record_value is None):
    return new_person_value
  
  # If new person value has not been set, and record value is not none
  elif (new_person_value is None) and (record_value != None):
    #print(f"Setting: {new_person_value} to {record_value}")
    return record_value

  elif (new_person_value == record_value):
    return new_person_value

  # If new person value is not an array, record value is not none, and the record value is not equal new person value
  elif (new_person_value != None) and (not isinstance(new_person_value, list)) and (record_value != None) and (record_value != new_person_value):
     return [new_person_value, record_value]
  
  # If new person value is an array, record value is not none, and record value is not in new person value array
  elif (new_person_value != None) and (isinstance(new_person_value, list)) and (record_value != None) and (not (record_value in new_person_value)):
    new_person_value.append(record_value)
    return new_person_value
  
  elif (new_person_value != None) and (isinstance(new_person_value, list)) and (record_value != None) and (record_value in new_person_value):
    return new_person_value
  
  else:
    #print("HIT ELSE")
    #print(f"New: {new_person_value}, Record: {record_value}")
    return new_person_value

def set_fields(new_person_value, record_value):
  if isinstance(record_value, list):
    for value in record_value:
      new_person_value = set_field(new_person_value, value)

  return new_person_value

def not_blank(val):
  if val != "" and val != None:
    return True
  return False

def get_from_bap_dict(mission, number, bap_dict):
  if(mission in bap_dict.keys()):
    if(number in bap_dict[mission].keys()):
      if(bap_dict[mission][number] != None):
        return bap_dict[mission][number]
  return None

# Combine all records found for a person into single Person object
def create_person(record_arr):

  if (record_arr == None):
    return None

# person = Person(line_id, gender=None, race=None, origin=None, age=None,\
        # record_year=None, baptismal_number=None, baptismal_mission=None,\
        # location=None,\
        # first_name=None, last_name=None, \

        # spouse_first=None, spouse_last=None, \
        # spouse_baptismal_mission = None, spouse_baptismal_number=None,\

        # father_first=None, father_last=None, \
        # father_baptismal_mission = None, father_baptismal_number=None, \

        # mother_first=None, mother_last=None, \
        # mother_baptismal_mission = None, mother_baptismal_number=None,\

        # children=None, children_objs=[], \

        # record_mission=None, \
        # record_type=None, )

  new_person = Person(line_id, gender=None, race=None, origin=None, age=None,\
        record_year=None, baptismal_number=None, baptismal_mission=None,\
        location=None,\
        first_name=None, last_name=None, \

        spouse_first=None, spouse_last=None, \
        spouse_baptismal_mission = None, spouse_baptismal_number=None,\

        father_first=None, father_last=None, \
        father_baptismal_mission = None, father_baptismal_number=None, \

        mother_first=None, mother_last=None, \
        mother_baptismal_mission = None, mother_baptismal_number=None,\

        children=[],\

        record_mission=None, \
        record_type=None)
  
  #print(f"Record Arr: {record_arr}")
  #Make the record_arr a list if its not already
  if not isinstance(record_arr, List):
    record_arr = [record_arr]
    
    
  for record in record_arr:
    new_person.gender = set_field(new_person.gender, record.gender)
    new_person.race = set_fields(new_person.race, record.race)
    new_person.origin = set_field(new_person.origin, record.origin)
    new_person.birth_year_estimate = set_field(new_person.birth_year_estimate, record.birth_year_estimate)
    new_person.record_year = set_field(new_person.record_year, record.record_year)
    new_person.baptismal_number = set_field(new_person.baptismal_number, record.baptismal_number)
    new_person.baptismal_mission = set_field(new_person.baptismal_mission, record.baptismal_mission)
    new_person.location = set_field(new_person.location, record.location)
    new_person.first_name = set_field(new_person.first_name, record.first_name)
    new_person.last_name = set_field(new_person.last_name, record.last_name)
    new_person.spouse_first = set_field(new_person.spouse_first, record.spouse_first)
    new_person.spouse_last = set_field(new_person.spouse_last, record.spouse_last)
    new_person.spouse_obj = set_field(new_person.spouse_obj, record.spouse_obj)
    new_person.spouse_baptismal_mission = set_field(new_person.spouse_baptismal_mission, record.spouse_baptismal_mission)
    new_person.spouse_baptismal_number = set_field(new_person.spouse_baptismal_number, record.spouse_baptismal_number)
    new_person.previous_spouse_first = set_field(new_person.previous_spouse_first, record.previous_spouse_first)
    new_person.previous_spouse_last = set_field(new_person.previous_spouse_last, record.previous_spouse_last)
    new_person.previous_spouse_obj = set_field(new_person.previous_spouse_obj, record.previous_spouse_obj)
    new_person.previous_spouse_baptismal_mission = set_field(new_person.previous_spouse_baptismal_mission, record.previous_spouse_baptismal_mission)
    new_person.previous_spouse_baptismal_number = set_field(new_person.previous_spouse_baptismal_number, record.previous_spouse_baptismal_number)
    new_person.previous_spouse_death_mission = set_field(new_person.previous_spouse_death_mission, record.previous_spouse_death_mission)
    new_person.previous_spouse_death_number = set_field(new_person.previous_spouse_death_number, record.previous_spouse_death_number)
    new_person.father_first = set_field(new_person.father_first, record.father_first)
    new_person.father_last = set_field(new_person.father_last, record.father_last)
    new_person.father_obj = set_field(new_person.father_obj, record.father_obj)
    new_person.father_baptismal_mission = set_field(new_person.father_baptismal_mission, record.father_baptismal_mission)
    new_person.father_baptismal_number = set_field(new_person.father_baptismal_number, record.father_baptismal_number)
    new_person.mother_first = set_field(new_person.mother_first, record.mother_first)
    new_person.mother_last = set_field(new_person.mother_last, record.mother_last)
    new_person.mother_obj = set_field(new_person.mother_obj, record.mother_obj)
    new_person.mother_baptismal_mission = set_field(new_person.mother_baptismal_mission, record.mother_baptismal_mission)
    new_person.mother_baptismal_number = set_field(new_person.mother_baptismal_number, record.mother_baptismal_number)
    new_person.record_mission = set_field(new_person.record_mission, record.record_mission)
    new_person.record_type = set_field(new_person.record_type, record.record_type)

    for child in record.children:
      new_person.children.append(child)
      
    for child_obj in record.children_objs:
      new_person.children_objs.append(child_obj)

  return new_person


# first_names["FirstName"] =  [(assembledPerson, record_arr reference)]<-- An array of tuples containing an assembled person and a reference to their record arrays. IF A PERSON APPEARS WITH TWO FIRST NAMES, THEN THEIR TUPLE IS ATTACHED TO BOTH OF THOSE NAMES
first_names = {}

def add_to_first_names(record_arr):
  assembled_person = create_person(record_arr)
  if isinstance(assembled_person.first_name, list):
    for name in assembled_person.first_name:
      add_or_format_dict(name, assembled_person, record_arr)
  else:
    add_or_format_dict(assembled_person.first_name, assembled_person, record_arr)

def add_or_format_dict(first_name, assembled_person, record_arr):
  if not first_name in first_names:
    first_names[first_name] = []
    first_names[first_name].append((assembled_person, record_arr))
  else:
    first_names[first_name].append((assembled_person, record_arr))


# Reformat the ECPP Baptismal Mission/Baptismal Number dictionary to a first_name based dictionary
for mission in universal_families.keys():
  for number in universal_families[mission]:
    add_to_first_names(universal_family_lookup(mission, number))


#Test to make sure python passes arrays by reference the way I think it does.
universal_families["BP"]["6"]

#first_names["Joseph Maria"][0][1].append(Person(line_id=56565, first_name="I HATE MY LIFE2!!!!"))
print(create_person(first_names["Jose Maria"][0][1]).first_name)


# A basic attempt at finding people from the census data in the ECPP data

found_people = 0

def birth_year_about_eq(year1, year2):
  if year1 != None and year2 != None:
    if type(year1) != str and type(year2) != str:
      if (year1 in range(year2-1, year2+2)) or (year2 in range(year1-1, year1+2)):
        return True
  return False

def compare_field(census_value, universal_value, confidence, increase_amount):
  if (census_value != None) and (universal_value != None) \
  and census_value == universal_value:
    confidence += increase_amount
  return confidence

def confidence_is_person(census_person, universal_person):
  compared_fields = 9
  increase_amount = compared_fields/100
  confidence = 0

  # if gender not equal then RETURN 0 BECAUSE IF GENDERS DO NOT MATCH, THEN ITS NOT THE SAME PERSON
  if census_person.gender == "":
    census_person.gender = None
  if universal_person.gender == "":
    universal_person.gender = None

  if (census_person.gender != None) and (universal_person.gender != None) \
  and not census_person.gender == universal_person.gender:
    return 0

  # Start by last names comparing names if not blank
  if census_person.last_name == "":
    census_person.last_name = None
  if universal_person.last_name == "":
    universal_person.last_name = None

  if isinstance(universal_person.last_name, list):
    for universal_last in universal_person.last_name:
      confidence = compare_field(census_person.last_name, universal_last, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.last_name, universal_person.last_name, confidence, increase_amount)

  # Start by first names comparing names if not blank
  if census_person.first_name == "":
    census_person.first_name = None
  if universal_person.first_name == "":
    universal_person.first_name = None

  if isinstance(universal_person.first_name, list):
    for universal_first in universal_person.first_name:
      confidence = compare_field(census_person.first_name, universal_first, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.first_name, universal_person.first_name, confidence, increase_amount)

  # Start by comparing fathers last names names if not blank
  if census_person.father_last == "":
    census_person.father_last = None
  if universal_person.father_last == "":
    universal_person.father_last = None

  if isinstance(universal_person.father_last, list):
    for universal_f_last in universal_person.father_last:
      confidence = compare_field(census_person.father_last, universal_f_last, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.father_last, universal_person.father_last, confidence, increase_amount)
  
  # Start by comparing fathers first names names if not blank
  if census_person.father_first == "":
    census_person.father_first = None
  if universal_person.father_first == "":
    universal_person.father_first = None

  if isinstance(universal_person.father_first, list):
    for universal_f_first in universal_person.father_first:
      confidence = compare_field(census_person.father_first, universal_f_first, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.father_first, universal_person.father_first, confidence, increase_amount)
  
  # Start by comparing mothers last names names if not blank
  if census_person.mother_last == "":
    census_person.mother_last = None
  if universal_person.mother_last == "":
    universal_person.mother_last = None

  if isinstance(universal_person.mother_last, list):
    for universal_m_last in universal_person.mother_last:
      confidence = compare_field(census_person.mother_last, universal_m_last, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.mother_last, universal_person.mother_last, confidence, increase_amount)
  
  # Start by comparing mothers first names names if not blank
  if census_person.mother_first == "":
    census_person.mother_first = None
  if universal_person.mother_first == "":
    universal_person.mother_first = None

  if isinstance(universal_person.mother_first, list):
    for universal_m_first in universal_person.mother_first:
      confidence = compare_field(census_person.mother_first, universal_m_first, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.mother_first, universal_person.mother_first, confidence, increase_amount)
  
  """
  # Compare location if not blank THIS ASSUMES NO ONE MOVED TO GET MARRIED   <----- REVISIT THIS!!!
  if (not census_person.location == "") and (not universal_person.location == "") \
  and census_person.location == universal_person.location:
    confidence += increase_amount"""

  # Start by comparing spouse last names if not blank
  if census_person.spouse_last == "":
    census_person.spouse_last = None
  if universal_person.spouse_last == "":
    universal_person.spouse_last = None

  if isinstance(universal_person.spouse_last, list):
    for universal_s_last in universal_person.spouse_last:
      confidence = compare_field(census_person.spouse_last, universal_s_last, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.spouse_last, universal_person.spouse_last, confidence, increase_amount)

  # Start by comparing spouse first names if not blank
  if census_person.spouse_first == "":
    census_person.spouse_first = None
  if universal_person.spouse_first == "":
    universal_person.spouse_first = None

  if isinstance(universal_person.spouse_first, list):
    for universal_s_first in universal_person.spouse_first:
      confidence = compare_field(census_person.spouse_first, universal_s_first, confidence, increase_amount)
  else:
    confidence = compare_field(census_person.spouse_first, universal_person.spouse_first, confidence, increase_amount)

  # Start by comparing birth years if not blank
  if census_person.birth_year_estimate == "":
    census_person.birth_year_estimate = None
  if universal_person.birth_year_estimate == "":
    universal_person.birth_year_estimate = None

  if isinstance(universal_person.birth_year_estimate, list):
    for universal_birth in universal_person.birth_year_estimate:
      if birth_year_about_eq(census_person.birth_year_estimate, universal_birth):
        confidence += increase_amount
  else:
    if birth_year_about_eq(census_person.birth_year_estimate, universal_person.birth_year_estimate):
        confidence += increase_amount
    
  return confidence


# Might not need
def same_person(census_person, marriage_person, required_confidence):
  confidence = confidence_is_person(census_person, marriage_person)
  if confidence >= required_confidence:
    return True
  return False


# Calculate a confidence level for every person, compared to every person
def calculate_confidences():
  # Iterate over every person in the census
  for census_first_name in census_families.keys():
    for census_person in census_families[census_first_name]:
      
      if census_person.first_name in first_names.keys():
        for ecpp_person in first_names[census_person.first_name]:
          
          confidence = confidence_is_person(census_person, ecpp_person[0])

          if census_person.highest_match == None:
            census_person.highest_match = (confidence, ecpp_person)
          else:
            if confidence > census_person.highest_match[0]:
              census_person.highest_match = (confidence, ecpp_person)


calculate_confidences()


#Adds the census record to a persons record_arr

count = 0
razon_match = 0
alt_races = []
for name, persons in census_families.items():
  for census_person in census_families[name]:
    if census_person.highest_match != None and census_person.highest_match[0] > .3:
      count+=1
      match_assembled_before_aggregating_race = census_person.highest_match[1][0]

      #See if matched person is Razon
      if isinstance(match_assembled_before_aggregating_race.race, list):
        race_list = match_assembled_before_aggregating_race.race
        razon_spellings = ["razon", "rason", "[razon]", "[rason]", "r[azon]", "razon [mulatos]"]
        for race in race_list:
          if race.lower() in razon_spellings:
            razon_match += 1
            break
          else:
            if race.lower not in alt_races:
              alt_races.append(race.lower())
        

      #Add the census record to the record_arr of the matched person
      ecpp_record_arr = census_person.highest_match[1][1]
      ecpp_record_arr.append(census_person)

      assembled_w_race = create_person(ecpp_record_arr)
      print("-------------------------------")
      assembled_w_race.print_all()
      print("-------------------------------")

matches_found = 0
confidence_threshold = 50

for family, persons in census_families.items():
  for person in persons:
    if (not person.highest_match == None) \
    and person.highest_match[0] >= confidence_threshold:
      matches_found += 1
      print(f"{person} ... {person.highest_match[1]}")

print(matches_found)

#This next section is necessary because the create_person function does not create a new person for every "attached" person. Example. The children of a created_person is still an agregate of that childs references.

#created_by_bap["Mission"]["Baptism Number"] = CreatedPerson
created_by_bap = {}

#unregisted_people["First Name"] = People[]
unregistered_people = {}

#print(universal_family_lookup("BP", "141"))
def create_all_registered_people():
  for mission in universal_families.keys():
    for number in universal_families[mission].keys():
      record_arr = universal_family_lookup(mission, number)
      add_to_created_by_bap(create_person(record_arr))

create_all_registered_people()

multiple_baps = []

def connect_all_fathers():
  for mission in created_by_bap.keys():
    for number in created_by_bap[mission].keys():

      half_assembled_father = create_person(created_by_bap[mission][number].father_obj)

      #If a father has multiple baptismal missions and numbers, then skip it, we'll handle this later... It only happens 23 times
      if half_assembled_father != None and (isinstance(half_assembled_father.baptismal_mission, List) or isinstance(half_assembled_father.baptismal_number, List)):
        multiple_baps.append(half_assembled_father)
        break

      #If the father has a baptismal mission and number, look him up in the dict and reference it
      if half_assembled_father != None and not_blank(half_assembled_father.baptismal_mission) and not_blank(half_assembled_father.baptismal_number):
        assembled_father = person_lookup(half_assembled_father.baptismal_mission, half_assembled_father.baptismal_number)
        created_by_bap[mission][number].assembled_father_obj = assembled_father
    
      #If the father does not have a baptismal mission or number
      else:
        if half_assembled_father != None:
          #This is the case where the father has no baptismal number or mission, but his children do. If they do, then look them up (because they have already been created) and assign them to the father.
          if len(half_assembled_father.children_objs) > 0:
            for child_record_arr in half_assembled_father.children_objs:

              #Create a child based off what the father knows
              half_assembled_child = create_person(child_record_arr)
              
              #if that created child has a baptismal mission and number look him up and set him
              if not_blank(half_assembled_child.baptismal_mission) and not_blank(half_assembled_child.baptismal_number):
                half_assembled_father.assembled_children_objs.append(created_by_bap[half_assembled_child.baptismal_mission][half_assembled_child.baptismal_number])
              
              #If the half assembled child doesn't have a mission or number, then add what we know about him to the fathers list of children
              else:
                half_assembled_father.assembled_children_objs.append(half_assembled_child)
              
        #Assign the father to the child.
        created_by_bap[mission][number].assembled_father_obj = half_assembled_father

connect_all_fathers()

multiple_baps = []

def connect_all_mothers():
  for mission in created_by_bap.keys():
    for number in created_by_bap[mission].keys():

      half_assembled_mother = create_person(created_by_bap[mission][number].mother_obj)

      #If a mother has multiple baptismal missions and numbers, then skip it, we'll handle this later... It only happens 23 times
      if half_assembled_mother != None and (isinstance(half_assembled_mother.baptismal_mission, List) or isinstance(half_assembled_mother.baptismal_number, List)):
        multiple_baps.append(half_assembled_mother)
        break

      #If the mother has a baptismal mission and number, look him up in the dict and reference it
      if half_assembled_mother != None and not_blank(half_assembled_mother.baptismal_mission) and not_blank(half_assembled_mother.baptismal_number):
        assembled_mother = person_lookup(half_assembled_mother.baptismal_mission, half_assembled_mother.baptismal_number)
        created_by_bap[mission][number].assembled_mother_obj = assembled_mother
    
      #If the mother does not have a baptismal mission or number
      else:
        if half_assembled_mother != None:
          #This is the case where the mother has no baptismal number or mission, but his children do. If they do, then look them up (because they have already been created) and assign them to the mother.
          if len(half_assembled_mother.children_objs) > 0:
            for child_record_arr in half_assembled_mother.children_objs:

              #Create a child based off what the mother knows
              half_assembled_child = create_person(child_record_arr)
              
              #if that created child has a baptismal mission and number look him up and set him
              if not_blank(half_assembled_child.baptismal_mission) and not_blank(half_assembled_child.baptismal_number):
                half_assembled_mother.assembled_children_objs.append(created_by_bap[half_assembled_child.baptismal_mission][half_assembled_child.baptismal_number])
              
              #If the half assembled child doesn't have a mission or number, then add what we know about him to the mothers list of children
              else:
                half_assembled_mother.assembled_children_objs.append(half_assembled_child)
              
        #Assign the mother to the child.
        created_by_bap[mission][number].assembled_mother_obj = half_assembled_mother

connect_all_mothers()


multiple_baps = []

def connect_all_spouses():
  for mission in created_by_bap.keys():
    for number in created_by_bap[mission].keys():
      #print(f"Mission: {mission}, Number: {number}")
      #print(created_by_bap[mission][number].assembled_spouse_obj == None)
      if created_by_bap[mission][number].assembled_spouse_obj == None:

        half_assembled_spouse = create_person(created_by_bap[mission][number].spouse_obj)

        #print(half_assembled_spouse)

        if half_assembled_spouse != None and (isinstance(half_assembled_spouse.baptismal_mission, List) or isinstance(half_assembled_spouse.baptismal_number, List)):
          multiple_baps.append(half_assembled_spouse)
          break

        if half_assembled_spouse != None and not_blank(half_assembled_spouse.baptismal_mission) and not_blank(half_assembled_spouse.baptismal_number):
          #print(f"HalfMission: {half_assembled_father.baptismal_mission}, Number: {half_assembled_father.baptismal_number}")
          spouse_record_arr = universal_family_lookup(half_assembled_spouse.baptismal_mission, half_assembled_spouse.baptismal_number)
          created_by_bap[mission][number].assembled_spouse_obj = create_person(spouse_record_arr)
        else:
          created_by_bap[mission][number].assembled_spouse_obj = half_assembled_spouse

connect_all_spouses()

multiple_child_baps = []

def connect_all_children():
  for mission in created_by_bap.keys():
    for number in created_by_bap[mission].keys():
      #print(f"Mission: {mission}, Number: {number}")
      for child_record_arr in created_by_bap[mission][number].children_objs:

        half_assembled_child = create_person(child_record_arr)

        if half_assembled_child != None and (isinstance(half_assembled_child.baptismal_mission, List) or isinstance(half_assembled_child.baptismal_number, List)):
          multiple_child_baps.append(half_assembled_child)
          break

        if half_assembled_child != None and not_blank(half_assembled_child.baptismal_mission) and not_blank(half_assembled_child.baptismal_number):
          #print(f"HalfMission: {half_assembled_child.baptismal_mission}, Number: {half_assembled_child.baptismal_number}")
          child_record_arr = universal_family_lookup(half_assembled_child.baptismal_mission, half_assembled_child.baptismal_number)
          new_child = create_person(child_record_arr)
          
          #23 fathers have multiple missions and numbers, I'll deal with that later
          if not_blank(new_child.father_baptismal_mission) and not_blank(new_child.father_baptismal_number) and ((isinstance(new_child.father_baptismal_mission, List) or isinstance(new_child.father_baptismal_number, List))):
            pass

          #Look up childs father in the dict
          elif(not_blank(new_child.father_baptismal_mission) and not_blank(new_child.father_baptismal_number)):
            new_child.assembled_father_obj = person_lookup(new_child.father_baptismal_mission, new_child.father_baptismal_number)
          
          #If he's not there, then take what we know about him and make him
          elif(new_child.father_obj != None):
            new_child.assembled_father_obj = create_person(new_child.father_obj)
          
          #Add child to dict
          add_to_created_by_bap(new_child)

          #Add child to parents assembled_children_objs[]
          created_by_bap[mission][number].assembled_children_objs.append(created_by_bap[half_assembled_child.baptismal_mission][half_assembled_child.baptismal_number])

        #If child doesnt exist in the dict, use the already made half assembled child.
        else:
          
          #look for his dad
          if(not_blank(half_assembled_child.father_baptismal_mission) and not_blank(half_assembled_child.father_baptismal_number)):
            half_assembled_child.assembled_father_obj = person_lookup(half_assembled_child.father_baptismal_mission, half_assembled_child.father_baptismal_number)
          
          #make dad if need be
          elif(half_assembled_child.father_obj != None):
            half_assembled_child.assembled_father = create_person(half_assembled_child.father_obj)
          
          #attached child to new_person
          created_by_bap[mission][number].assembled_children_objs.append(half_assembled_child)

connect_all_children()


created_by_bap = {}
modified = []
def reset_created_by_bap():
  create_all_registered_people()
  connect_all_fathers()
  connect_all_mothers()
  connect_all_spouses()
  connect_all_children()
reset_created_by_bap()


modified = []

def reset_mods():
  for person in modified:
    person.generation = 0
    person.visited = False

#This is the not sucky way of doing it!
def BFSParents(person):
  queue = []
  queue.append(person)
  highest_gen_parent = person
  person.visited = True
  person.set_parent_gen()

  while queue:
    #print("Queue Contains: "+str(len(queue)))
    person = queue.pop(0)
    #print("-------------------------")
    #person.print_all()
    #print("-------------------------")
    father = person.assembled_father_obj
    mother = person.assembled_mother_obj
    #for parent in [father, mother]:
    for parent in [mother]:
      if parent != None and parent.visited == False:
        queue.append(parent)
        parent.visited = True
        parent.set_parent_gen()
        #print(f"Highest Gen: {highest_gen_parent.generation} ParentFirst: {parent.first_name} ParentGeneration: {parent.generation}")
        if parent.generation > highest_gen_parent.generation:
          highest_gen_parent = parent

        modified.append(parent)
        if father != None:
          modified.append(father)
        if mother != None:
          modified.append(mother)

  return highest_gen_parent

def findFamilyHead(person):
  head = BFSParents(person)
  #reset_mods()
  #modified = []
  return head


# BFS for children of person
def childrenBFS(person, largest_gen_child, current_gen=0):
  queue = []
  queue.append(person)
  person.visited = True
  person.set_childens_gen()
  person.set_childrens_race()

  while queue:
    person = queue.pop(0)
    #print(person)

    for child in person.assembled_children_objs:
      if child.visited == False:
        queue.append(child)
        child.visited = True
        child.set_childens_gen()
        child.set_childrens_race()
        if child.generation > largest_gen_child.generation:
          largest_gen_child = child
  return largest_gen_child


def allFamiliesChildrenBFS(family_heads, largest_gen_child):
  for head in family_heads:
    largest_gen_child = childrenBFS(head, largest_gen_child)
  return largest_gen_child


#Set the race of every person in the dataset
reset_mods()
modified=[]

for mission in created_by_bap:
  for number in created_by_bap[mission]:
    person = person_lookup(mission, number)
    head = findFamilyHead(person)
    childrenBFS(head, person)

    reset_mods()
    modified=[]

print("Ready!")


app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!<p>"

@app.route("/testPerson")
def test_person():
    person = person_lookup("SCL", "729")
    head = findFamilyHead(person)
    result = head.export_person_string()
    return result

@app.route("/getPerson")
def getPerson():
    baptismal_mission = request.args.get("baptismal_mission")
    baptismal_number = request.args.get("baptismal_number")

    person = person_lookup(baptismal_mission, baptismal_number)
    head = findFamilyHead(person)
    result = head.export_person_string()
    return result[:len(result)-1]

