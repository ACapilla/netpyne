"""
test_validate.py

Testing code for Validation class

Contributors: mitra.sidddhartha@gmail.com
"""
import unittest
import numbers
import sys
import os
import traceback

VALID_SHAPES = ['cuboid', 'ellipsoid', ' cylinder']
POP_NUMCELLS_PARAMS = ['Density','NumCells','GridSpacing']

MESSAGE_TYPE_WARN = "WARNING"
MESSAGE_TYPE_ERROR = "ERROR"
MESSAGE_TYPE_INFO = "INFO"

TEST_TYPE_EXISTS = "testExists" # parameter must exist
TEST_TYPE_EXISTS_IN_LIST = "Exists in list" # ex. one of paremters number, density, gridspacing must be specified
TEST_TYPE_IS_VALID_RANGE = "Is Valid Range" # like [0,1]
TEST_TYPE_IN_RANGE = "In Range" # ex. xnormRange must be between 0 and 1

TEST_TYPE_EQ = "Equal to" # ex. equal to

TEST_TYPE_GT = "Greater than" # ex. greater than
TEST_TYPE_GTE = "Greater than or equal to" # ex. greater than or equal to

TEST_TYPE_GT_ZERO = "Greater than zero" # ex. greater than
TEST_TYPE_GTE_ZERO = "Greater than or equal to zero" # ex. greater than or equal to

TEST_TYPE_LT = "Lesser than" # ex. lesser than
TEST_TYPE_LTE = "Lesser than or equal to" # ex. lesser than or equal to

TEST_TYPE_LT_ZERO = "Lesser than zero" # ex. lesser than
TEST_TYPE_LTE_ZERO = "Lesser than or equal to zero" # ex. lesser than or equal to

TEST_TYPE_IS_DICT = "Is dictionary" # must be a dictionary

TEST_TYPE_IS_NUMERIC = "Is Numeric" # must be numeric
TEST_TYPE_IS_FLOAT = "Is Float" # must be float
TEST_TYPE_IS_INT = "Is Integer" # must be integer
TEST_TYPE_IS_CHARACTER = "Is Character" # must be char [a-z][A-Z]
TEST_TYPE_VALUE_LIST = "Value List" # must be in valid values list
TEST_TYPE_SPECIAL = "Special" # special method, method name provided

testFunctionsMap = {}

testFunctionsMap [TEST_TYPE_EXISTS] = "testExists"
testFunctionsMap [TEST_TYPE_EXISTS_IN_LIST] = "testExistsInList"
testFunctionsMap [TEST_TYPE_IS_VALID_RANGE] = "testIsValidRange"
testFunctionsMap [TEST_TYPE_IN_RANGE] = "testInRange"
testFunctionsMap [TEST_TYPE_EQ] = "testEquals"

testFunctionsMap [TEST_TYPE_GT] = "testGt"
testFunctionsMap [TEST_TYPE_GTE] = "testGte"
testFunctionsMap [TEST_TYPE_GTE_ZERO] = "testGteZero"

testFunctionsMap [TEST_TYPE_LT] = "testGt"
testFunctionsMap [TEST_TYPE_LTE] = "testGte"
testFunctionsMap [TEST_TYPE_LTE_ZERO] = "testGteZero"

testFunctionsMap [TEST_TYPE_VALUE_LIST] = "testExists"
testFunctionsMap [TEST_TYPE_EXISTS_IN_LIST] = "testExistsInList"

class TestTypeObj(object):

    def __init__(self):

        self.testType = '' # test name
        self.params = ''
        self.errorMessages = []

    def __unicode__(self):
        return str(self.testType)

    def testExists(self, val,params):
        try:
            assert (val in params), val + " must be specified."
        except AssertionError as e:
            # if self.verboseFlag:
            #     traceback.print_exc(file=sys.stdout)
            e.args += ('val',)
            raise

    def testExistsInList(self, val,params):
        # print ( " !!!! in exists test !!!! ")
        # print ( " val = " + str(type(val)) + " params = " + str(params))
        try:
            assert any([x in params for x in val]), " At least one of " + str(val) + " must be specified in " + str(params) + "."
            # print (" **^^^^*** Test passed !!!")
        except:
            # print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testIsValidRange(self, val,params): # TEST_TYPE_IS_VALID_RANGE
        # print ( " !!!! in valid range test !!!! ")
        # print ( " val = " + str(val) + " params = " + str(params))
        # print ( " $$$ params[val] = " + str(params[val]))
        #+ " len = " + str(len(params[val])) )
        try:
            if val in params:
                assert (isinstance(params[val], list)) # chk if list
                assert (len(params[val]) == 2) # chk if len is 2 ( is range)
                assert ( params[val][0] < params[val][1]) # check if lower < upper value in range
            # print (" **^^^^*** Test passed !!!")
        except:
            # print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testInRange(self, val,range, params): # TEST_TYPE_IN_RANGE
        print ( " !!!! in -- range test !!!! ")
        print ( " val = " + str(val) + " range = " + str(range) + " params = " + str(params))
        try:
            if val in params:
                print ( " $$$ params[val] = " + str(params[val])  + " type = " + str(type(params[val]))  )
                assert (params[val][0] >= range[0] and params[val][1] <= range[1])
                # print (" **^^^^*** Test passed !!!")
        except:
            # print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testEquals(self, val,compareVal):
        try:
            assert (val == compareVal)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testGt(self, val,compareVal): # TEST_TYPE_GT
        try:
            assert (val > compareVal)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testGte(self, val,compareVal): # TEST_TYPE_GTE
        try:
            assert (val >= compareVal)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testGteZero(self, val): # TEST_TYPE_GTE
        try:
            assert (val >= 0)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testGtZero(self, val): # TEST_TYPE_GT
        try:
            assert (val > 0)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testLt(self, val,compareVal): # TEST_TYPE_LT
        try:
            assert (val < compareVal)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testLte(self,val,compareVal): # TEST_TYPE_LTE
        try:
            assert (val <= compareVal)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testLteZero(self, val): # TEST_TYPE_LTE
        try:
            assert (val <= 0)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testLtZero(self,val): # TEST_TYPE_LTE
        try:
            assert (val < 0)
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testIsDict(self,val): # TEST_TYPE_IS_DICT
        try:
            assert (isinstance (val,dict))
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testIsNumeric(self,val): # TEST_TYPE_IS_DICT
        try:
            assert (isinstance (val,numbers.Number))
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testIsFloat(self,val): # TEST_TYPE_IS_FLOAT
        try:
            assert (isinstance (val,float))
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testIsInt(self,val): # TEST_TYPE_IS_INT
        try:
            assert (isinstance (val,int))
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testIsCharacter(self,val): # TEST_TYPE_IS_CHARACTER
        try:
            isascii = lambda s: len(s) == len(s.encode())
            assert (isascii (val))
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

    def testIsValueList(self,val, valList): # TEST_TYPE_VALUE_LIST
        try:
            assert (val in valList), val + " must be in list " + (",").join()
            print (" **^^^^*** Test passed !!!")
        except:
            print (" ***###*** Test failed !!!")
            traceback.print_exc(file=sys.stdout)

# Tests that are defined for each set of parameters
class TestObj(object):

    def __init__(self):

        self.testName = '' # test name

        self.testParameterType = '' # test parameter, type string, list
        self.testParameterValue = '' # test parameter value, like 'shape'
        self.testParameterValueList = '' # test parameter value list, like ['density', 'numCells','gridSpacing']
        self.testParameterDictString = '' # for nested dicts like ['shape']['geom']

        self.testTypes = [] # list of be multiple tests
        self.testValueList = [] # could be restricted list like ['cuboid','ellipsoid','cylinder']
        self.testValueRange = [] # could be restricted range like [0,1]

        self.compareValueString = "" # variable name - like netParams.sizeX, or value
        self.compareValueDataType = "" # data type of compare value ( string or list or dict
        self.compareValueType = "" # eval (if compareValueString is string or int or float
        self.conditionString = "" # condition for test

        self.messageText = [] # error message text - array for each test
        self.errorMessageLevel = [] # info, warn, error - array for each test

    def __unicode__(self):
        return str(self.testName)

class NetPyneTestObj(object):

    def __init__(self, verboseFlag = False):

        # The tests to be conducted on the netpyne params
        self.testParamsMap = {}
        self.simConfig = ''  # object of class SimConfig to store simulation configuration
        self.netParams = ''
        self.testTypeObj = TestTypeObj()
        self.loadTests()
        self.verboseFlag = verboseFlag

    def loadTests(self):

        if self.verboseFlag:
            print (" *** Loading tests *** ")
        self.loadPopTests() # load pop tests
        self.loadNetTests() # load net tests
        self.loadCellTests() # load cell tests
        self.loadConnTests() # load conn tests
        if self.verboseFlag:
            print (" *** Finish loading tests *** ")

    def runTests(self):

        if self.verboseFlag:
            print (" *** Running tests *** ")
        self.runPopTests() # run pop tests
        self.runNetTests() # run net tests
        self.runCellTests() # run cell tests
        self.runConnTests() # run conn tests

        if self.verboseFlag:
            print (" *** Finished running tests *** ")

    def loadPopTests(self):

        if self.verboseFlag:
            print (" *** Loading pop tests *** ")

        # initialiase list of test objs
        self.testParamsMap["pop"] = {}

        ##cell model test
        testObj = TestObj()
        testObj.testName = "cellModelTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "cellModel"
        testObj.testTypes = [TEST_TYPE_EXISTS]
        testObj.messageText = ["No Cell Model specified in population paramters."]
        testObj.errorMessageLevel = [MESSAGE_TYPE_ERROR]

        self.testParamsMap["pop"]["cellModelTest"] = testObj

        ##volume params test
        testObj = TestObj()
        testObj.testName = "volumeParamsTest"
        testObj.testParameterType = "list"
        testObj.testParameterValueList = ['density','numCells','gridSpacing']
        testObj.testTypes = [TEST_TYPE_EXISTS_IN_LIST]
        testObj.messageText = ["One of the following must be specified in parameters:"]
        testObj.errorMessageLevel = [MESSAGE_TYPE_ERROR]

        self.testParamsMap["pop"]["volumeParamsTest"] = testObj

        # xnormrange test
        testObj = TestObj()
        testObj.testName = "xNormRangeTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "xnormRange"
        testObj.testTypes = [TEST_TYPE_IS_VALID_RANGE, TEST_TYPE_IN_RANGE]
        testObj.testValueRange = "[0,1]"
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["pop"]["xNormRangeTest"] = testObj

        # ynormrange test
        testObj = TestObj()
        testObj.testName = "yNormRangeTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "ynormRange"
        testObj.testTypes = [TEST_TYPE_IS_VALID_RANGE, TEST_TYPE_IN_RANGE]
        testObj.testValueRange = "[0,1]"
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["pop"]["yNormRangeTest"] = testObj

        # znormrange test
        testObj = TestObj()
        testObj.testName = "zNormRangeTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "znormRange"
        testObj.testTypes = [TEST_TYPE_IS_VALID_RANGE, TEST_TYPE_IN_RANGE]
        testObj.testValueRange = "[0,1]"
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["pop"]["zNormRangeTest"] = testObj

        # xrange test
        testObj = TestObj()
        testObj.testName = "xRangeTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "xRange"
        testObj.testTypes = [TEST_TYPE_IS_VALID_RANGE, TEST_TYPE_IN_RANGE]
        testObj.testValueRange = "[0,self.netParams.sizeX]"
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["pop"]["xRangeTest"] = testObj

        # yrange test
        testObj = TestObj()
        testObj.testName = "yRangeTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "yRange"
        testObj.testTypes = [TEST_TYPE_IS_VALID_RANGE, TEST_TYPE_IN_RANGE]
        testObj.testValueRange = "[0,self.netParams.sizeY]"
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["pop"]["yRangeTest"] = testObj

        # zrange test
        testObj = TestObj()
        testObj.testName = "zRangeTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "zRange"
        testObj.testTypes = [TEST_TYPE_IS_VALID_RANGE, TEST_TYPE_IN_RANGE]
        testObj.testValueRange = "[0,self.netParams.sizeX]"
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["pop"]["zRangeTest"] = testObj

        if self.verboseFlag:
            print (" *** Finished loading pop tests *** ")

    def loadNetTests(self):

        if self.verboseFlag:
            print (" *** Loading net tests *** ")

        self.testParamsMap["net"] = {}

        # sizeX test
        testObj = TestObj()
        testObj.testName = "sizeXTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "self.netParams.sizeX"
        testObj.testTypes = [TEST_TYPE_IS_INT, TEST_TYPE_GT_ZERO]
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["net"]["sizeXTest"] = testObj

        # sizeY test
        testObj = TestObj()
        testObj.testName = "sizeYTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "self.netParams.sizeY"
        testObj.testTypes = [TEST_TYPE_IS_INT, TEST_TYPE_GT_ZERO]
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["net"]["sizeYTest"] = testObj

        # sizeZ test
        testObj = TestObj()
        testObj.testName = "sizeZTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "self.netParams.sizeZ"
        testObj.testTypes = [TEST_TYPE_IS_INT, TEST_TYPE_GT_ZERO]
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["net"]["sizeZTest"] = testObj

        # shape test
        testObj = TestObj()
        testObj.testName = "shapeTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "self.netParams.shape"
        testObj.testTypes = [TEST_TYPE_VALUE_LIST]
        testObj.testValueList = VALID_SHAPES
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["net"]["shapeTest"] = testObj

        if self.verboseFlag:
            print (" *** Finished loading net tests *** ")

    def loadCellTests(self):

        if self.verboseFlag:
            print (" *** Loading cell tests *** ")

        self.testParamsMap["net"] = {}

        # condsTest test
        testObj = TestObj()
        testObj.testName = "condsTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "conds"
        testObj.testTypes = [TEST_TYPE_IS_DICT]
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["net"]["condsTest"] = testObj

        if self.verboseFlag:
            print (" *** Finished loading cell tests *** ")

    def loadCellTests(self):

        if self.verboseFlag:
            print (" *** Loading conn tests *** ")

        self.testParamsMap["net"] = {}

        # condsTest test
        testObj = TestObj()
        testObj.testName = "condsTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "conds"
        testObj.testTypes = [TEST_TYPE_IS_DICT]
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["cell"]["condsTest"] = testObj

        if self.verboseFlag:
            print (" *** Finished loading cell tests *** ")

    def loadConnTests(self):

        if self.verboseFlag:
            print (" *** Loading conn tests *** ")

        self.testParamsMap["conn"] = {}

        # condsTest test
        testObj = TestObj()
        testObj.testName = "preCondsTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "conds"
        testObj.testTypes = [TEST_TYPE_EXISTS]
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["conn"]["preCondsTest"] = testObj

        # condsTest test
        testObj = TestObj()
        testObj.testName = "postCondsTest"
        testObj.testParameterType = "string"
        testObj.testParameterValue = "conds"
        testObj.testTypes = [TEST_TYPE_EXISTS]
        testObj.errorMessageLevel = ["MESSAGE_TYPE_ERROR"]
        self.testParamsMap["conn"]["postCondsTest"] = testObj

        if self.verboseFlag:
            print (" *** Finished loading conn tests *** ")

    def runPopTests(self):

        if self.verboseFlag:
            print (" *** Running pop tests *** ")

        popParams = self.netParams.popParams
        for testName, popTestObj in self.testParamsMap["pop"].items():
            self.execRunTests(popTestObj, popParams)

        if self.verboseFlag:
            print (" *** Finished running pop tests *** ")

    def runNetTests(self):

        if self.verboseFlag:
            print (" *** Running net tests *** ")

        netParams = self.netParams
        print (self.testParamsMap)
        for testName, netTestObj in self.testParamsMap["net"].items():
            self.execRunTests(netTestObj, netParams)

        if self.verboseFlag:
            print (" *** Finished running net tests *** ")

    def runCellTests(self):

        if self.verboseFlag:
            print (" *** Running cell tests *** ")

        cellParams = self.netParams.cellParams
        for testName, cellTestObj in self.testParamsMap["cell"].items():
            self.execRunTests(cellTestObj, cellParams)

        if self.verboseFlag:
            print (" *** Finished running cell tests *** ")

    def runConnTests(self):

        if self.verboseFlag:
            print (" *** Running conn tests *** ")

        connParams = self.netParams.connParams
        for testName, connTestObj in self.testParamsMap["conn"].items():
            self.execRunTests(connTestObj, connParams)

        if self.verboseFlag:
            print (" *** Finished running conn tests *** ")

    def execRunTests(self, testObj, params):

        if self.verboseFlag:
            print (" *** executing individual tests *** ")

        for testType in testObj.testTypes:
            if self.verboseFlag:
                print ( " !!! testType = " + str(testType))

            if testType == TEST_TYPE_EXISTS:

                if isinstance(params, dict):
                    for paramLabel, paramValues in params.items():
                        if self.verboseFlag:
                            print ( " ***** running for parameter " + str(paramLabel))
                        try:
                            self.testTypeObj.testExists (testObj.testParameterValue,  paramValues)
                        except Exception as e:
                            print str(e)
                else:
                        print ( " ***** running for parameter " + str(params))
                        self.testTypeObj.testExists (testObj.testParameterValue,  paramValues)

            elif testType == TEST_TYPE_EXISTS_IN_LIST:

                if isinstance(params, dict):
                    for paramLabel, paramValues in params.items():
                        print ( " ***** running for parameter " + str(paramLabel))
                        self.testTypeObj.testExistsInList (testObj.testParameterValueList,  paramValues)
                else:
                        print ( " ***** running for parameter " + str(params))
                        self.testTypeObj.testExistsInList (testObj.testParameterValueList,  paramValues)

            elif testType == TEST_TYPE_IN_RANGE:

                if isinstance(params, dict):

                    for paramLabel, paramValues in params.items():
                        print ( " ***** running for parameter " + str(paramLabel))
                        self.testTypeObj.testInRange(testObj.testParameterValue, eval(testObj.testValueRange), paramValues)
                else:
                        print ( " ***** running for parameter " + str(params))
                        self.testTypeObj.testInRange(testObj.testParameterValue, eval(testObj.testValueRange), paramValues)

            elif testType == TEST_TYPE_IS_VALID_RANGE:

                if isinstance(params, dict):

                    for paramLabel, paramValues in params.items():
                        print ( " ***** running for parameter " + str(paramLabel))
                        self.testTypeObj.testIsValidRange(testObj.testParameterValue, paramValues)
                else:
                        print ( " ***** running for parameter " + str(params))
                        self.testTypeObj.testIsValidRange(testObj.testParameterValue, paramValues)

            elif testType == TEST_TYPE_IS_INT:

                if isinstance(params, dict):

                    print ( str ( type ( params )))
                    for paramLabel, paramValues in params.items():
                        print ( " ***** running for parameter " + str(paramLabel))
                        self.testTypeObj.testIsInt(testObj.testParameterValue, paramValues)
                else:
                        print ( " ***** running for parameter " + str(params))

                        paramName = eval(testObj.testParameterValue)
                        print ( " ***** running for parameter name " + str(paramName))

#                        paramValue = params.paramName

                        #print ( " ***** running for parameter value " + str(paramValue))
                        self.testTypeObj.testIsInt(paramName)

            elif testType == TEST_TYPE_GTE_ZERO:

                if isinstance(params, dict):

                    for paramLabel, paramValues in params.items():
                        print ( " ***** running for parameter " + str(paramLabel))
                        self.testTypeObj.testGteZero(testObj.testParameterValue, paramValues)
                else:
                        print ( " ***** running for parameter " + str(params))
                        paramName = eval(testObj.testParameterValue)
                        #paramValue = eval(params.paramName)
                        print ( " ***** running for parameter value " + str(paramName))

                        self.testTypeObj.testGteZero(paramName)
