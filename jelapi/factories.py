import factory
from faker_enum import EnumProvider

from tests.utils import get_standard_env, get_standard_node, get_standard_node_group

from . import classes

factory.Faker.add_provider(provider=EnumProvider)


class _JelasticEnvironmentFactory(factory.Factory):
    class Meta:
        model = classes.JelasticEnvironment


class _JelasticNodeGroupFactory(factory.Factory):
    class Meta:
        model = classes.JelasticNodeGroup

    nodeGroupType = factory.Faker(
        "enum", enum_cls=classes.JelasticNodeGroup.NodeGroupType
    )


class _JelasticNodeFactory(factory.Factory):
    class Meta:
        model = classes.JelasticNode

    nodeType = factory.Faker("enum", enum_cls=classes.JelasticNode.NodeType)


class _JelasticMountPointFactory(factory.Factory):
    class Meta:
        model = classes.JelasticMountPoint

    nodeType = factory.Faker("enum", enum_cls=classes.JelasticNode.NodeType)


class JelasticEnvironmentFactory(_JelasticEnvironmentFactory):
    @classmethod
    def _after_postgeneration(obj, instance, create, results=None):
        """
        Generate a standard Env
        """
        instance.update_from_env_dict(get_standard_env())
        ngs = {}
        for key in ["cp", "sqldb", "storage"]:
            ng = JelasticNodeGroupFactory()
            ng._nodeGroupType = next(
                (
                    ng
                    for ng in classes.JelasticNodeGroup.NodeGroupType
                    if ng.value == key
                ),
            )
            ng.attach_to_environment(instance)

            for n in ng.nodes:
                if key in ["cp", "sqldb"]:
                    n._nodeType = classes.JelasticNode.NodeType.DOCKER
                elif key == "storage":
                    n._nodeType = classes.JelasticNode.NodeType.STORAGE

                # Set different Ids
                if key == "cp":
                    n._id = 110
                if key == "sqldb":
                    n._id = 120
                if key == "storage":
                    n._id = 130

            ngs[key] = ng

        instance.nodeGroups = ngs
        instance.copy_self_as_from_api("nodeGroups")


class JelasticNodeFactory(_JelasticNodeFactory):
    @classmethod
    def _after_postgeneration(obj, instance, create, results=None):
        """
        Generate a standard Node
        """
        instance.update_from_env_dict(get_standard_node())
        assert instance.is_from_api


class JelasticNodeGroupFactory(_JelasticNodeGroupFactory):
    @classmethod
    def _after_postgeneration(obj, instance, create, results=None):
        """
        Generate a standard NodeGroup, with one node of a random nodeType
        It can be set according to needs afterwards.
        """
        instance.update_from_env_dict(
            get_standard_node_group(node_group_type=instance.nodeGroupType)
        )
        node = JelasticNodeFactory()

        # Set different Ids
        if instance.nodeGroupType.value == "cp":
            node._id = 110
        if instance.nodeGroupType.value == "sqldb":
            node._id = 120
        if instance.nodeGroupType.value == "storage":
            node._id = 130

        node.attach_to_node_group(instance)
        instance.copy_self_as_from_api("nodes")
