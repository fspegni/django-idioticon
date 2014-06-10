#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_idioticon
--------------

Tests for `idioticon` models module.
"""
import unittest
from django.utils.text import slugify
import faker

from idioticon import models


class TestIdioticonGetTerm(unittest.TestCase):

    def setUp(self):
        self.manager = models.Term.objects
        self.fake = faker.Faker()

    def _create_random_term(self, main_term=None):
        fields = {}
        while True:
            name = self.fake.word()
            fields['key'] = slugify(name)
            if main_term:
                fields['main_term'] = main_term
            else:
                fields['name'] = name
                fields['definition'] = self.fake.text()

            if not self.manager.filter(key=fields['key']).exists():
                return self.manager.create(**fields)

    def _create_aliases(self, term, nb=0):
        aliases = []
        for _ in range(nb or self.fake.random_int(1, 5)):
            aliases.append(self._create_random_term(term))
        return aliases

    def _create_main_terms(self, nb=0):
        main_terms = []
        for _ in range(nb or self.fake.random_int(1, 10)):
            main_terms.append(self._create_random_term())
        return main_terms

    def _create_terms(self, terms_nb=0, aliases_nb=0):
        all_terms = self._create_main_terms(terms_nb)
        terms_with_aliases = all_terms[:self.fake.randomize_nb_elements(len(all_terms), le=True)]
        aliases_by_term_key = {}
        for t in terms_with_aliases:
            aliases_by_term_key[t.key] = self._create_aliases(t, aliases_nb)
            all_terms += aliases_by_term_key[t.key]
        return all_terms, aliases_by_term_key

    def test_get_main_term(self):

        terms, aliases = self._create_terms(10)

        for term in terms:
            if term.main_term:
                # is alias
                self.assertFalse(term.is_main_term)
                self.assertTrue(term.is_alias)
                self.assertEqual(term.main_term, self.manager.get_term(term.key))
                self.assertEqual(term, self.manager.get_term(term.key, resolve_alias=False))

            else:
                # is main term
                self.assertTrue(term.is_main_term)
                self.assertFalse(term.is_alias)

    def test_alias_overriding(self):

        term = self._create_random_term()
        alias = self._create_random_term(term)
        alias.name = self.fake.word()
        alias.save()

        self.assertEqual(term, alias.main_term)

        self.assertNotEqual(term.name, alias.get_name())
        self.assertNotEqual(term.get_name(), alias.get_name())

        self.assertEqual(term.definition, alias.get_definition())
        self.assertEqual(term.get_definition(), alias.get_definition())

    def test_term_does_not_exist_exception(self):
        self.assertRaises(models.Term.DoesNotExist, self.manager.get_term, 'not-existing-term')
        self.assertEqual(None, self.manager.get_term('not-existing-term', soft_error=True))


class TestIdioticonShortcuts(unittest.TestCase):

    def setUp(self):
        models.Term.objects.all().delete()

    def _create_term(self, key='my-term', name='My term', definition='Just a description'):
        return models.Term.objects.create(
            key=key,
            name=name,
            definition=definition
        )

    def test_add_term(self):
        term = models.add_term('my-term', 'My term', 'Just a description')
        self.assertTrue(term)
        self.assertFalse(models.add_term('my-term', '...', '...'))

    def test_set_term(self):
        term = self._create_term('my-term')
        self.assertTrue(term)
        name = term.name
        updated_term = models.set_term(term, name='My new term')
        self.assertTrue(updated_term)
        self.assertIs(term, updated_term)
        self.assertEqual(updated_term.name, 'My new term')
        self.assertNotEqual(updated_term.name, name)

        self.assertTrue(models.set_term('not-existent-term', name='...'))

    def test_update_term(self):
        term = self._create_term('my-term')
        self.assertTrue(term)

        old_name = term.name
        updated_term = models.update_term(term, 'Pretty title')
        self.assertTrue(updated_term)
        self.assertIs(term, updated_term)
        self.assertEqual(updated_term.name, term.name)
        self.assertNotEqual(old_name, term.name)

        self.assertFalse(models.update_term('not-existent-term', '...'))

    def test_delete_term(self):
        term = self._create_term()
        self.assertTrue(term)
        models.delete_term(term.key)
        term = models.get_term('my-term')
        self.assertFalse(term)

    def test_add_alias(self):
        term = self._create_term()
        alias = self._create_term('my-alias', 'My alias', 'Just a alias description')
        self.assertTrue(term)
        self.assertTrue(alias)
        self.assertTrue(models.add_alias(term, alias))
        self.assertEqual(term, alias.main_term)