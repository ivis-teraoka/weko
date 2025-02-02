import argparse
import properties
import sys
from properties import property_config

from invenio_db import db
from weko_records.models import ItemTypeProperty


def main():
    try:
        exclusion_list = [int(x) for x in property_config.EXCLUSION_LIST]
        type_list = ['overwrite_all', 'only_add_new', 'only_specified']
        # Read parameters.
        parser = argparse.ArgumentParser()
        parser.add_argument('reg_type', action='store')
        try:
            args = parser.parse_args()
        except BaseException:
            print('Please input parameter of register type.')
            print('List of valid parameters [{}].'.format(','.join(type_list)))
            sys.exit(0)
        if args.reg_type == 'overwrite_all':
            truncate_table()
            register_properties_from_folder(exclusion_list)
            db.session.commit()
        elif args.reg_type == 'only_add_new':
            exclusion_list += get_properties_id()
            register_properties_from_folder(exclusion_list)
            db.session.commit()
        elif args.reg_type == 'only_specified':
            specified_list = property_config.SPECIFIED_LIST
            del_properties(specified_list)
            exclusion_list += get_properties_id()
            register_properties_from_folder(exclusion_list, specified_list)
            db.session.commit()
        else: 
            print('Please input parameter of register type.')
            print('List of valid parameters [{}].'.format(','.join(type_list)))
            sys.exit(0) 
    except Exception as ex:
        print(ex)


def truncate_table():
    db.session.execute('TRUNCATE item_type_property;')
    db.session.commit()


def get_properties_id():
    properties = db.session.query(ItemTypeProperty.id).all()
    return [x.id for x in properties]


def del_properties(del_list):
    db.session.query(ItemTypeProperty).filter(ItemTypeProperty.id.in_(del_list)).delete(synchronize_session='fetch')


def register_properties_from_folder(exclusion_list, specified_list=[]):
    reg_list = []
    prop_list = list()
    for i in dir(properties):
        prop = getattr(properties, i)
        if getattr(prop, 'property_id', None) and prop.property_id:
            prop_id = int(prop.property_id)
            if (prop_id not in exclusion_list) \
                    or (prop_id in specified_list):
                prop_list.append(dict(
                    id=prop_id,
                    name=prop.name_ja,
                    schema=prop.schema(multi_flag=False),
                    form=prop.form(multi_flag=False),
                    forms=prop.form(multi_flag=True),
                    delflg=False
                ))
                reg_list.append(prop_id)
    if prop_list:
        db.session.execute(ItemTypeProperty.__table__.insert(), prop_list)
    db.session.execute("SELECT setval('item_type_property_id_seq', 10000, true);")

    reg_list.sort()
    print('Processed id list: ', reg_list)


if __name__ == '__main__':
    main()