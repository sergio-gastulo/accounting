$cmd = {
	param($x)
	return [double] $x
}

echo $cmd.Invoke(1).GetType()

# IsPublic IsSerial Name                                     BaseType
# -------- -------- ----                                     --------
# True     True     Collection`1                             System.Object
