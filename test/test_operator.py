# -*- coding: utf-8 -*-

# Copyright 2018 IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

import unittest
from collections import OrderedDict
import itertools
from test.common import QISKitAcquaTestCase

import numpy as np
from qiskit.tools.qi.pauli import Pauli, label_to_pauli

from qiskit_acqua import Operator
from qiskit_acqua import get_variational_form_instance


class TestOperator(QISKitAcquaTestCase):
    """Operator tests."""

    def setUp(self):
        np.random.seed(0)

        num_qubits = 4
        m_size = np.power(2, num_qubits)
        matrix = np.random.rand(m_size, m_size)
        self.qubitOp = Operator(matrix=matrix)

    def test_real_eval(self):
        depth = 1
        var_form = get_variational_form_instance('RYRZ')
        var_form.init_args(self.qubitOp.num_qubits, depth)
        circuit = var_form.construct_circuit(np.array(np.random.randn(var_form.num_parameters)))
        # self.qubitOp.coloring = None
        execute_config_ref = {'shots': 1, 'skip_translation': False}
        execute_config = {'shots': 10000, 'skip_translation': False}
        reference = self.qubitOp.eval('matrix', circuit, 'local_statevector_simulator', execute_config_ref)[0]
        reference = reference.real

        paulis_mode = self.qubitOp.eval('paulis', circuit, 'local_qasm_simulator', execute_config)
        grouped_paulis_mode = self.qubitOp.eval('grouped_paulis', circuit, 'local_qasm_simulator', execute_config)

        paulis_mode_p_3sigma = paulis_mode[0] + 3 * paulis_mode[1]
        paulis_mode_m_3sigma = paulis_mode[0] - 3 * paulis_mode[1]

        grouped_paulis_mode_p_3sigma = grouped_paulis_mode[0] + 3 * grouped_paulis_mode[1]
        grouped_paulis_mode_m_3sigma = grouped_paulis_mode[0] - 3 * grouped_paulis_mode[1]
        self.assertLessEqual(reference, paulis_mode_p_3sigma.real)
        self.assertGreaterEqual(reference, paulis_mode_m_3sigma.real)
        self.assertLessEqual(reference, grouped_paulis_mode_p_3sigma.real)
        self.assertGreaterEqual(reference, grouped_paulis_mode_m_3sigma.real)

        execute_config = {'shots': 10000, 'skip_translation': True}
        paulis_mode = self.qubitOp.eval('paulis', circuit, 'local_qasm_simulator', execute_config)
        grouped_paulis_mode = self.qubitOp.eval('grouped_paulis', circuit, 'local_qasm_simulator', execute_config)

        paulis_mode_p_3sigma = paulis_mode[0] + 3 * paulis_mode[1]
        paulis_mode_m_3sigma = paulis_mode[0] - 3 * paulis_mode[1]

        grouped_paulis_mode_p_3sigma = grouped_paulis_mode[0] + 3 * grouped_paulis_mode[1]
        grouped_paulis_mode_m_3sigma = grouped_paulis_mode[0] - 3 * grouped_paulis_mode[1]
        self.assertLessEqual(reference, paulis_mode_p_3sigma.real, "With skip_translation on")
        self.assertGreaterEqual(reference, paulis_mode_m_3sigma.real, "With skip_translation on")
        self.assertLessEqual(reference, grouped_paulis_mode_p_3sigma.real, "With skip_translation on")
        self.assertGreaterEqual(reference, grouped_paulis_mode_m_3sigma.real, "With skip_translation on")

    def test_exact_eval(self):
        depth = 1
        var_form = get_variational_form_instance('RYRZ')
        var_form.init_args(self.qubitOp.num_qubits, depth)
        circuit = var_form.construct_circuit(np.array(np.random.randn(var_form.num_parameters)))

        execute_config = {'shots': 1, 'skip_translation': False}
        matrix_mode = self.qubitOp.eval('matrix', circuit, 'local_statevector_simulator', execute_config)[0]
        non_matrix_mode = self.qubitOp.eval('paulis', circuit, 'local_statevector_simulator', execute_config)[0]
        diff = abs(matrix_mode - non_matrix_mode)
        self.assertLess(diff, 0.01, "Values: ({} vs {})".format(matrix_mode, non_matrix_mode))

        execute_config = {'shots': 1, 'skip_translation': True}
        non_matrix_mode = self.qubitOp.eval('paulis', circuit, 'local_statevector_simulator', execute_config)[0]
        diff = abs(matrix_mode - non_matrix_mode)
        self.assertLess(diff, 0.01, "With skip_translation on, Values: ({} vs {})".format(matrix_mode, non_matrix_mode))

    def test_create_from_paulis_0(self):
        """
            test with single paulis
        """
        num_qubits = 4
        for pauli_label in itertools.product('IXYZ', repeat=num_qubits):
            coeff = np.random.random(1)[0]
            pauli_term = [coeff, label_to_pauli(pauli_label)]
            op = Operator(paulis=[pauli_term])

            op.convert('paulis', 'matrix')
            op.convert('paulis', 'grouped_paulis')

            depth = 1
            var_form = get_variational_form_instance('RYRZ')
            var_form.init_args(op.num_qubits, depth)
            circuit = var_form.construct_circuit(np.array(np.random.randn(var_form.num_parameters)))
            execute_config = {'shots': 1, 'skip_translation': False}
            matrix_mode = op.eval('matrix', circuit, 'local_statevector_simulator', execute_config)[0]
            non_matrix_mode = op.eval('paulis', circuit, 'local_statevector_simulator', execute_config)[0]

    def test_create_from_matrix(self):
        """
            test with matrix initialization
        """
        for num_qubits in range(1, 6):
            m_size = np.power(2, num_qubits)
            matrix = np.random.rand(m_size, m_size)

            op = Operator(matrix=matrix)
            op.convert('matrix', 'paulis')
            op.convert('matrix', 'grouped_paulis')
            depth = 1
            var_form = get_variational_form_instance('RYRZ')
            var_form.init_args(op.num_qubits, depth)
            circuit = var_form.construct_circuit(np.array(np.random.randn(var_form.num_parameters)))

            execute_config = {'shots': 1, 'skip_translation': False}
            matrix_mode = op.eval('matrix', circuit, 'local_statevector_simulator', execute_config)[0]
            non_matrix_mode = op.eval('paulis', circuit, 'local_statevector_simulator', execute_config)[0]

    def test_multiplication(self):
        """
            test multiplication
        """
        pauli_a = 'IXYZ'
        pauli_b = 'ZYIX'
        coeff_a = 0.5
        coeff_b = 0.5
        pauli_term_a = [coeff_a, label_to_pauli(pauli_a)]
        pauli_term_b = [coeff_b, label_to_pauli(pauli_b)]
        opA = Operator(paulis=[pauli_term_a])
        opB = Operator(paulis=[pauli_term_b])
        newOP = opA * opB
        # print(newOP.print_operators())

        self.assertEqual(1, len(newOP.paulis))
        self.assertEqual(0.25, newOP.paulis[0][0])
        self.assertEqual('ZZYY', newOP.paulis[0][1].to_label())

    def test_addition(self):
        """
            test addition
        """
        pauli_a = 'IXYZ'
        pauli_b = 'ZYIX'
        coeff_a = 0.5
        coeff_b = 0.5
        pauli_term_a = [coeff_a, label_to_pauli(pauli_a)]
        pauli_term_b = [coeff_b, label_to_pauli(pauli_b)]
        opA = Operator(paulis=[pauli_term_a])
        opB = Operator(paulis=[pauli_term_b])
        newOP = opA + opB

        self.assertEqual(2, len(newOP.paulis))

        pauli_c = 'IXYZ'
        coeff_c = 0.25
        pauli_term_c = [coeff_c, label_to_pauli(pauli_c)]
        newOP += Operator(paulis=[pauli_term_c])

        self.assertEqual(2, len(newOP.paulis))
        self.assertEqual(0.75, newOP.paulis[0][0])

    def test_zero_coeff(self):
        """
            test addition
        """
        pauli_a = 'IXYZ'
        pauli_b = 'IXYZ'
        coeff_a = 0.5
        coeff_b = -0.5
        pauli_term_a = [coeff_a, label_to_pauli(pauli_a)]
        pauli_term_b = [coeff_b, label_to_pauli(pauli_b)]
        opA = Operator(paulis=[pauli_term_a])
        opB = Operator(paulis=[pauli_term_b])
        newOP = opA + opB

        self.assertEqual(1, len(newOP.paulis), "{}".format(newOP.print_operators()))

    def test_dia_matrix(self):
        """
            test conversion to dia_matrix
        """
        num_qubits = 4
        pauli_term = []
        for pauli_label in itertools.product('IZ', repeat=num_qubits):
            coeff = np.random.random(1)[0]
            pauli_term.append([coeff, label_to_pauli(pauli_label)])
        op = Operator(paulis=pauli_term)

        op.convert('paulis', 'matrix')
        op.convert('paulis', 'grouped_paulis')
        op._to_dia_matrix('paulis')

        self.assertEqual(op.matrix.ndim, 1)

        num_qubits = 4
        pauli_term = []
        for pauli_label in itertools.product('YZ', repeat=num_qubits):
            coeff = np.random.random(1)[0]
            pauli_term.append([coeff, label_to_pauli(pauli_label)])
        op = Operator(paulis=pauli_term)

        op.convert('paulis', 'matrix')
        op.convert('paulis', 'grouped_paulis')
        op._to_dia_matrix('paulis')

        self.assertEqual(op.matrix.ndim, 2)


if __name__ == '__main__':
    unittest.main()
