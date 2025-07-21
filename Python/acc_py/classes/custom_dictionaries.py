import json

class CustomDictionaries:
    def __init__(self, path: str):
        # Month dictionary for translation from ENG to SPA
        self.months_es = {
                1: "Enero",
                2: "Febrero",
                3: "Marzo",
                4: "Abril",
                5: "Mayo",
                6: "Junio",
                7: "Julio",
                8: "Agosto",
                9: "Septiembre",
                10: "Octubre",
                11: "Noviembre",
                12: "Diciembre"
            }
        self.categories = self.create_json(path)


    def create_json(self, path: str) -> dict[str, str]:
        """
        Loads JSON from `path` and returns the JSON parsed as follows:
        * The pattern `key: {sname, description}` is mapped to `sname: description`
        * The pattern `key: {skey1: {sname, desc}, skey2: {sname, desc}}` is mapped to `sname1: desc1, sname2, desc2` (flattened)
        """
        
        shortname_descript_dict = {}

        with open(path,'r') as file:
            for item_dict in json.load(file):
                subcategories = item_dict.get("subcategories")
                if subcategories:
                    for item in subcategories:
                        shortname_descript_dict.update({item["shortname"]: item["description"]})
                else:
                    shortname_descript_dict.update({item_dict["shortname"]: item_dict["description"]})

        return shortname_descript_dict