// Boston MSA median household income by household size
// Source: U.S. Census ACS 1-year, Table B19019
// size1 derived as: median_income_2_person * 0.67 (proxy — 1-person not in source data)

export const householdIncomeBySize = [
  { year: 2005, allHouseholds: 42562, size1: 19333, size2: 28856, size3: 55241, size4: 54372, size5: 51174 },
  { year: 2006, allHouseholds: 47974, size1: 20282, size2: 30271, size3: 60275, size4: 56419, size5: 68657 },
  { year: 2007, allHouseholds: 50476, size1: 22404, size2: 33439, size3: 62391, size4: 67413, size5: 51984 },
  { year: 2008, allHouseholds: 51688, size1: 23473, size2: 35035, size3: 67629, size4: 64900, size5: 75743 },
  { year: 2009, allHouseholds: 55979, size1: 25879, size2: 38625, size3: 73543, size4: 64727, size5: 70455 },
  { year: 2010, allHouseholds: 49893, size1: 19640, size2: 29313, size3: 62418, size4: 70748, size5: 65699 },
  { year: 2011, allHouseholds: 49081, size1: 19068, size2: 28459, size3: 65886, size4: 52015, size5: 71439 },
  { year: 2012, allHouseholds: 51642, size1: 22560, size2: 33672, size3: 66426, size4: 57621, size5: 74095 },
  { year: 2013, allHouseholds: 53583, size1: 23963, size2: 35766, size3: 67734, size4: 62326, size5: 65062 },
  { year: 2014, allHouseholds: 56902, size1: 21733, size2: 32437, size3: 75365, size4: 67339, size5: 69394 },
  { year: 2015, allHouseholds: 58263, size1: 25197, size2: 37607, size3: 80436, size4: 75067, size5: 76258 },
  { year: 2016, allHouseholds: 63621, size1: 24910, size2: 37179, size3: 90800, size4: 80244, size5: 86214 },
  { year: 2017, allHouseholds: 66758, size1: 24237, size2: 36175, size3: 89500, size4: 87210, size5: 86871 },
  { year: 2018, allHouseholds: 71834, size1: 25128, size2: 37505, size3: 94408, size4: 101131, size5: 90977 },
  { year: 2019, allHouseholds: 79018, size1: 27962, size2: 41734, size3: 104883, size4: 99193, size5: 142556 },
  { year: 2020, allHouseholds: 76298, size1: 27811, size2: 41509, size3: 102147, size4: 98858, size5: 105667 },
  { year: 2021, allHouseholds: 79283, size1: 34282, size2: 51167, size3: 104809, size4: 96948, size5: 119266 },
  { year: 2022, allHouseholds: 86331, size1: 36514, size2: 54499, size3: 114707, size4: 98572, size5: 130757 },
  { year: 2023, allHouseholds: 96931, size1: 36581, size2: 54599, size3: 130740, size4: 121570, size5: 144746 },
];

export const householdSizeOptions = [
  {
    id: 'size1',
    label: 'Single person',
    key: 'size1',
    income: 36581,
    targetHomePrice: 499000,
    bedroomContext: 'studio or 1BR',
    priceNote: 'est. based on Greater Boston median condo, 2023',
  },
  {
    id: 'size2',
    label: 'Two people',
    key: 'size2',
    income: 54599,
    targetHomePrice: 599000,
    bedroomContext: '1BR–2BR',
    priceNote: 'Greater Boston median condo sale price, 2023 (Warren Group)',
  },
  {
    id: 'size3',
    label: 'Three people',
    key: 'size3',
    income: 130740,
    targetHomePrice: 749000,
    bedroomContext: '2BR',
    priceNote: 'est. based on Greater Boston median condo, 2023',
  },
  {
    id: 'size4',
    label: 'Four people',
    key: 'size4',
    income: 121570,
    targetHomePrice: 899000,
    bedroomContext: '3BR',
    priceNote: 'est. based on Greater Boston median condo, 2023',
  },
  {
    id: 'size5',
    label: 'Five or more',
    key: 'size5',
    income: 144746,
    targetHomePrice: 1050000,
    bedroomContext: '3BR+',
    priceNote: 'est. based on Greater Boston median condo, 2023',
  },
];
