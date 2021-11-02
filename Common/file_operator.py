import yaml
import os


def split_file(file_path):
    filepath, temp_file_name = os.path.split(file_path)
    filename, extension = os.path.splitext(temp_file_name)
    return filepath, filename, extension


class YamlDescriptor:

    def __init__(self, f_get, f_set):
        self.f_get = f_get
        self.f_set = f_set

    def __get__(self, instance, owner):
        return self.f_get(instance)

    def __set__(self, instance, value):
        self.f_set(instance, value)


class YamlOperator:
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        f = open(self.file_path, 'r')
        yaml_obj = yaml.safe_load(f)
        f.close()
        return yaml_obj

    def write(self, content):
        with open(self.file_path, 'w')as f1:
            yaml.safe_dump(content, f1)


class YamlHandler(YamlOperator):

    def __init__(self, file_path: str, yaml_dict=None, parent="", parent_obj=None):
        super().__init__(file_path)
        self.parent = parent
        self.parent_obj = parent_obj
        self.yaml_dict = yaml_dict if yaml_dict else self.read()
        self.__obj_type = str(type(self.yaml_dict))

    def __getattr__(self, item):
        self.parent = item
        if not isinstance(self.yaml_dict, dict):
            raise TypeError("{} must be a <dict> but {}".format(self.__str__(), self.__obj_type))
        yaml_obj = self.yaml_dict.get(item, False)
        if yaml_obj is False:
            raise KeyError("{} has no attribute {}".format(self.__str__(), item))
        return YamlHandler(file_path=self.file_path, yaml_dict=yaml_obj, parent=self.parent, parent_obj=self)

    def __str__(self):
        return "<{} Object> Type: {} ".format(self.parent, self.__obj_type)

    def save(self):
        if not self.parent_obj:
            with open(self.file_path, 'w')as f1:
                yaml.safe_dump(self.yaml_dict, f1)
            return
        return self.parent_obj.save()

    def __get_value(self):
        return self.yaml_dict

    def __set_value(self, value):
        if self.parent:
            self.parent_obj.yaml_dict[self.parent] = value
        else:
            self.yaml_dict = value

    value = YamlDescriptor(__get_value, __set_value)


if __name__ == '__main__':
    y = YamlHandler(r"/Test_Data/global_config.yaml")
    print(y.value)
    y.value = {'global_config': {'config': [{'config': 1}, {'config2': 2}], 'result': "None"}}
    print(y.global_config.config.value)
    y.global_config.config.value = [1, 2, 3]
    print(y.value)
    print(y.global_config.config.value)
    y.save()