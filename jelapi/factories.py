import factory
from faker_enum import EnumProvider

from tests.utils import get_standard_env, get_standard_node, get_standard_node_group

from . import classes

factory.Faker.add_provider(provider=EnumProvider)


class _JelasticEnvironmentFactory(factory.Factory):
    class Meta:
        model = classes.JelasticEnvironment

    jelastic_env = get_standard_env()


class _JelasticNodeGroupFactory(factory.Factory):
    class Meta:
        model = classes.JelasticNodeGroup

    nodeGroup = factory.Faker("enum", enum_cls=classes.JelasticNodeGroup.NodeGroupType)


class _JelasticNodeFactory(factory.Factory):
    class Meta:
        model = classes.JelasticNode

    nodeType = factory.Faker("enum", enum_cls=classes.JelasticNode.NodeType)


class JelasticEnvironmentFactory(_JelasticEnvironmentFactory):
    @classmethod
    def _after_postgeneration(obj, instance, create, results=None):
        """
        Generate a standard Env
        """
        ngs = {}
        for key in ["cp", "sqldb", "storage"]:
            ng = JelasticNodeGroupFactory()
            ng.set_environment(instance)

            for n in ng.nodes:
                if key in ["cp", "sqldb"]:
                    n._nodeType = classes.JelasticNode.NodeType.DOCKER
                elif key == "storage":
                    n._nodeType = classes.JelasticNode.NodeType.STORAGE

            ngs[key] = ng

        instance.nodeGroups = ngs


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
        instance.update_from_env_dict(get_standard_node_group())
        node = JelasticNodeFactory()
        node.set_node_group(instance)
        instance.nodes = [node]
        instance.copy_self_as_from_api("nodes")
