
def get_invoice_data_list():
		invoices_list = [
				{"sales_invoice": "SI-MUS-00798", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00795", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00781", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00769", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00762", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00747", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00746", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00745", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00742", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00734", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00733", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00732", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00703", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00684", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00665", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00663", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00658", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00656", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00646", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00641", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00589", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00587", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00586", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00581", "bill_to": "C00276"},
				{"sales_invoice": "SI-MUS-00573", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02681", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02703", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02705", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02706", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02753", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02781", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02800", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02813", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02859", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03565", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03541", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03505", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03489", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03444", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03412", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03395", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03391", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03376", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03370", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03359", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03355", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03332", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03323", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03318", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03304", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03295", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03244", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03238", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03210", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03194", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03180", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03152", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03145", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03128", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03091", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03064", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03061", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03060", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02888", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-03006", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02979", "bill_to": "C00276"},
				{"sales_invoice": "SI-RAS-02950", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-03945", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-03963", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04071", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04036", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04105", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04157", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04141", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04140", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04154", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04220", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04329", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04328", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04375", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04387", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04382", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04467", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04454", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04438", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04590", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04568", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04638", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04672", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04671", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04725", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04722", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04853", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04846", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04840", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04836", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-04961", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05017", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05083", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05082", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05080", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05063", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05111", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05229", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05220", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05442", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05375", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05475", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05456", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05518", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05588", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05616", "bill_to": "C00276"},
				{"sales_invoice": "SI-SAJ-05606", "bill_to": "C00276"}
			]

		invoices_list.extend([
			{'sales_invoice': 'SI-MUS-00768', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00721', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00718', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00692', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00657', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00640', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00619', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00613', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00570', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00555', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00543', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00541', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-MUS-00536', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02664', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02707', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02709', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02714', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02725', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02736', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02754', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02758', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02759', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02762', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02791', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02792', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02795', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02797', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02799', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02803', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02814', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02821', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03551', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03544', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03533', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03532', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03509', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03400', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03375', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03374', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03336', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03335', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03271', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03242', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03224', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03193', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03169', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03151', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03130', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03097', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03080', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03065', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03056', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03047', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03015', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03013', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03011', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03008', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03005', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02991', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02984', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02982', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02977', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02976', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02975', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02967', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02947', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02944', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02943', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02936', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02935', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02933', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02902', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02881', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02878', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02876', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02874', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02873', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02872', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02836', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02834', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02833', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02826', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02789', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02738', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02870', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02734', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02733', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02724', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02716', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02700', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02691', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02688', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03566', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03539', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03520', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03507', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03481', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02884', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03468', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03464', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03456', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03452', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03451', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03438', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03411', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03404', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03363', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03349', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03345', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03326', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03317', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03309', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03307', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03289', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03265', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03263', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03260', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03246', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03211', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03205', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03198', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03142', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03134', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03122', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03114', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03112', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03111', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03110', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03105', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03103', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03099', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03084', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03049', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03041', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03032', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03029', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03017', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-03012', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02995', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02985', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02983', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02960', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02958', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02913', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02909', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02905', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02903', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02895', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02894', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-RAS-02893', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-04294', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-04526', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-04525', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-04515', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-04701', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-05094', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-05086', 'bill_to': 'C01053'},
			{'sales_invoice': 'SI-SAJ-05391', 'bill_to': 'C01053'}
		])

		invoices_list.extend(
			[
				{
					"sales_invoice": "SI-MUS-00521",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-MUS-00487",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-MUS-00456",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-MUS-00442",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-MUS-00440",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-MUS-00430",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-MUS-00414",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-MUS-00400",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01732",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02517",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02454",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02451",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02424",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02392",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02379",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02373",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02327",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02325",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02268",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02261",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02246",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02137",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02133",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02121",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02023",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02022",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-02013",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01986",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01979",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01967",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01939",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01902",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-04028",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-04027",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-04026",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-04019",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-04017",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-04016",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02061",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-04004",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03990",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03953",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03951",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03859",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03807",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03789",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03785",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03783",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03781",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03779",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03757",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02135",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03725",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03714",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03713",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03712",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03711",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03710",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03705",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03704",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03703",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03696",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03692",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03673",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03670",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03648",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03619",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03601",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03573",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03957",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03493",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03492",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03491",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03489",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03488",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03487",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03486",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03485",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03483",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03482",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03481",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03438",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03436",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03435",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03434",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03425",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03419",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03390",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03384",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03383",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03382",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03381",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03380",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03379",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03378",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03377",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03376",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03375",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03374",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03373",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03371",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03370",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03368",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03367",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03366",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03356",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03349",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03319",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03241",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03240",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03239",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03238",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03237",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03233",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03203",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03078",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03059",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02959",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02941",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02904",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02379",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02820",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02679",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02577",
					"bill_to": "C00276"
				}
			]
		)

		invoices_list.extend(
				[
					{
						"sales_invoice": "SI-MUS-00511",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00510",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00499",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00490",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00486",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00483",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00473",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00471",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00359",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00448",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00437",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00436",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00395",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00388",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00386",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00383",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00381",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00380",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-MUS-00371",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01710",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01712",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01723",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01731",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01736",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02528",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02527",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02526",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02525",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02520",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02512",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02505",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02489",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02477",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02467",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02464",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02462",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02430",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02420",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02417",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02416",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02415",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02405",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02394",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02384",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02362",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02361",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02354",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02350",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02349",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02321",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02318",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02317",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02316",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02309",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02307",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02304",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02295",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02287",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02284",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02282",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02275",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02272",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02266",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02264",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02260",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02250",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02247",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02244",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02240",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02236",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02234",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02230",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02218",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02217",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02207",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02192",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02185",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02184",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02181",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02178",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02167",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02161",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02154",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02149",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02142",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02139",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02138",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02136",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02135",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02131",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02129",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02126",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02125",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02119",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02117",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02116",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02114",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02112",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02111",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02110",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02096",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02095",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02086",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02084",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02066",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02064",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02063",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02058",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02054",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02050",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02046",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02028",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02020",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02019",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02016",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02011",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02010",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02006",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-02001",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01993",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01991",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01983",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01970",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01764",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01766",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01767",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01768",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01770",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01771",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01968",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01966",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01964",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01963",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01962",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01958",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01779",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01788",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01794",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01799",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01800",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01953",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01946",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01933",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01932",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01931",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01928",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01927",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01926",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01924",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01916",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01908",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01901",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01896",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01895",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01893",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01884",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01813",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01878",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01875",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01873",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01872",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01870",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01869",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01868",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01867",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01865",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01864",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01863",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01845",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01837",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01835",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01834",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01817",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01830",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01828",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01827",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01826",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01823",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01820",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-RAS-01818",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-04003",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-02062",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03995",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03988",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03974",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03962",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03956",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03941",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03578",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03566",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03346",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-03093",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-02915",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-02912",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-02846",
						"bill_to": "C01053"
					},
					{
						"sales_invoice": "SI-SAJ-02579",
						"bill_to": "C01053"
					}
				]
		)

		invoices_list.extend(
			[
				{
					"sales_invoice": "SI-RAS-01025",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01097",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01100",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01115",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00569",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00589",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00599",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00606",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00639",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00671",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00704",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00708",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00714",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01565",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02794",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03014",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03127",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03008",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-03189",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02808",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-00026",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-00028",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-00029",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-00029-1",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-02451",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-00050",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01326",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01332",
					"bill_to": "C00276"
				}
			]
		)

		invoices_list.extend(
			[
		{
			"sales_invoice": "SI-RAS-01384",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01387",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01388",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01026",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01042",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01043",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01051",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01054",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01055",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01061",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01070",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01084",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01087",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01105",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01111",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01132",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00539",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00553",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00559",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00565",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00588",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00593",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00610",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00611",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00616",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00617",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00622",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00626",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00631",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00632",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00637",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00640",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00641",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00643",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00658",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00668",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00670",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00698",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-00699",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01383",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01407",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01434",
			"bill_to": "C01053"
		},
		{
			"sales_invoice": "SI-RAS-01606",
			"bill_to": "C01053"
		}
		]
			)

		invoices_list.extend(
			[
				{
					"sales_invoice": "SI-SAJ-00931",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-00932",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01019",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01023",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01030",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01045",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01046",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01134",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01159",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01179",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01188",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01189",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01429",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01287",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01296",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01297",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-SAJ-01308",
					"bill_to": "C00276"
				}
			]
		)

		invoices_list.extend(
			[
				{
					"sales_invoice": "SI-SAJ-01002",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-01289-1",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-02401",
					"bill_to": "C01053"
				}
			]
		)

		invoices_list.extend(
			[
				{
					"sales_invoice": "SI-RAS-01637",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01567",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01525",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01519",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01469",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01450",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01435",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01411",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01381",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01331",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01326",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01221",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01208",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01193",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01175",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-01041",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00982",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00976",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00974",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00939",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00910",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00853",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00885",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00878",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00876",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00865",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00864",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00812",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00811",
					"bill_to": "C00276"
				},
				{
					"sales_invoice": "SI-RAS-00798",
					"bill_to": "C00276"
				}
			]
		)

		invoices_list.extend(
			[
				{
					"sales_invoice": "SI-RAS-01714",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01708",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01707",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01704",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01700",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01696",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01695",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01694",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01678",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01675",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01669",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01667",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01664",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01661",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01659",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01622",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01617",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01596",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01595",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01592",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01590",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01586",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01581",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01577",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01575",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01574",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01563",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01550",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01545",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01527",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01520",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01518",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01509",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01508",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01505",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01444",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01441",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01436",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01426",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01397",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01374",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01373",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01367",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01363",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01357",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01356",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01354",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01353",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01349",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01348",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01338",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01329",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01314",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01313",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01308",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01307",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01274",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01272",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01265",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01263",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01261",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01260",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01259",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01254",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01238",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01235",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01219",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01202",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01183",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01164",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01145",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01143",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-01000",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00993",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00989",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00977",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00975",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00965",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00963",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00947",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00946",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00912",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00871",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00822",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00816",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00790",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00782",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00757",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00749",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00748",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-00742",
					"bill_to": "C01053"
				}
			]
		)

		invoices_list.extend([
			{
				"sales_invoice": "SI-MUS-01064",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01062",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01057",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01053",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07608",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07605",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07604",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07603",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07602",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04398",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07548",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04386",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07501",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07497",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07492",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01044",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01043",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04349",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01036",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04316",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04292",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07397",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01019",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04254",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07344",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01013",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-01010",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07260",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04246",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04243",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07247",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04235",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04234",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04233",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04206",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07196",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07148",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07147",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00985",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00983",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00982",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00979",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07082",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04175",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-07023",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04148",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04137",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04123",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06884",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06878",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00958",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04077",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00945",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04058",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06745",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06688",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06684",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00932",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-04004",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06620",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03989",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06578",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03967",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03966",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03964",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03962",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03933",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03932",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03922",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00920",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03915",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06417",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06366",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03854",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00892",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00879",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00877",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03844",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03835",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03823",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03817",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06222",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06220",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06208",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06086",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03813",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03806",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03799",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03797",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03790",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03786",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00873",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00869",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00867",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00865",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00863",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00861",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00858",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-06058",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05958",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05950",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05949",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03689",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03683",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03676",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05889",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05878",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03645",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05841",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05831",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05819",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05818",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05817",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05816",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05815",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03636",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03635",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05793",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03624",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05763",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03616",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03611",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00838",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00820",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-MUS-00815",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-SAJ-05718",
				"bill_to": "C00276"
			},
			{
				"sales_invoice": "SI-RAS-03569",
				"bill_to": "C00276"
			}
		]
		)

		invoices_list.extend(
			[
				{
					"sales_invoice": "SI-RAS-04416",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04406",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04395",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04387",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04384",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04381",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-01041",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04345",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04344",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04339",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04332",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04326",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04324",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04301",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04294",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04290",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04281",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-01020",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04256",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-07351",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-07283",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-01008",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04222",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04209",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04204",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04200",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04199",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04198",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04196",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-07177",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-07166",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00981",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-07083",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04173",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04163",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04161",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04157",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04143",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04131",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-06975",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-02400",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00963",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00959",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04090",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04080",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00949",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04065",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04032",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-04030",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00940",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00936",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03992",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03987",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03976",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03950",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-06533",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03940",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03927",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03925",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03921",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00916",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03913",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-06340",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03873",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03843",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03841",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03830",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-06206",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03808",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03794",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03785",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03769",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00850",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03758",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03736",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03730",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03729",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03727",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03720",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03718",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03705",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03704",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03694",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03684",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03663",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03662",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03652",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03651",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03650",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03644",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-05807",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03621",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-05768",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-05740",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00824",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00814",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-MUS-00813",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-SAJ-05713",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03607",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03600",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03596",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03593",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03589",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03587",
					"bill_to": "C01053"
				},
				{
					"sales_invoice": "SI-RAS-03578",
					"bill_to": "C01053"
				}
			]
		)

		return invoices_list